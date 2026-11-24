import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from painel.config import TIPO_OFERTA_INTEGRAL, TIPO_OFERTA_PARCIAL
from painel.dados import DATA_DIR, carregar_ensino_integral_ideb


COR_INTEGRAL = "#1f77b4"
COR_PARCIAL = "#ff7f0e"
ANOS_IDEB_OFERTA = [2017, 2019, 2023, 2025]


ARQUIVOS_SECAO = {
    "oferta_anual.parquet": {
        "ano", "total_escolas", "integrais", "parciais", "pct_integrais",
        "pct_mat_integrais",
    },
    "ideb_por_oferta.parquet": {
        "ano", "tipo_oferta", "total_escolas", "com_ideb", "cobertura_pct",
        "media_ideb",
    },
    "testes_ideb_oferta.parquet": {
        "ano", "n_integral", "n_parcial", "diferenca", "p_valor",
    },
}


def _validar_arquivos_secao():
    faltantes = [
        nome for nome in ARQUIVOS_SECAO
        if not (DATA_DIR / nome).exists()
    ]
    if faltantes:
        raise FileNotFoundError(
            "Arquivos necessários para a seção Oferta integral plena e IDEB ausentes: "
            + ", ".join(faltantes)
        )


def _validar_colunas_secao(dados):
    for (nome, esperadas), quadro in zip(ARQUIVOS_SECAO.items(), dados):
        ausentes = esperadas - set(quadro.columns)
        if ausentes:
            raise ValueError(
                f"{nome} não contém as colunas esperadas: "
                f"{', '.join(sorted(ausentes))}"
            )
        if nome == "testes_ideb_oferta.parquet" and "IC 95%" not in quadro:
            if not {"ic95_inferior", "ic95_superior"}.issubset(quadro.columns):
                raise ValueError(
                    f"{nome} precisa conter 'IC 95%' ou as colunas "
                    "'ic95_inferior' e 'ic95_superior'."
                )


def _recorte_anos(quadro, anos, nome):
    recorte = quadro.loc[quadro["ano"].isin(anos)].sort_values("ano").copy()
    faltantes = sorted(set(anos) - set(recorte["ano"]))
    if faltantes:
        raise ValueError(
            f"{nome} não contém os anos esperados: "
            f"{', '.join(map(str, faltantes))}"
        )
    return recorte


def _formatar_diferenca(valor):
    return f"{float(valor):+.3f}".replace(".", ",")


def _formatar_ic95(valor):
    if pd.isna(valor):
        return "—"
    try:
        inferior, superior = str(valor).strip("[]").split(";")
        return (
            f"[{float(inferior.replace(',', '.')):.3f}; "
            f"{float(superior.replace(',', '.')):.3f}]"
        ).replace(".", ",")
    except (AttributeError, ValueError):
        return str(valor)


def _formatar_p_valor(valor):
    if pd.isna(valor):
        return "—"
    texto = str(valor).strip()
    if texto.startswith("<"):
        limite = texto[1:].strip().replace(",", ".")
        try:
            if float(limite) <= 0.001:
                return "p < 0,001"
        except ValueError:
            pass
        return texto.replace(".", ",")
    try:
        numero = float(texto.replace(",", "."))
    except ValueError:
        return texto
    if numero < 0.001:
        return "p < 0,001"
    return f"p = {numero:.3f}".replace(".", ",")


def _tabela_oferta_anual(oferta):
    tabela = oferta[
        ["ano", "total_escolas", "integrais", "pct_integrais", "parciais"]
    ].copy()
    tabela["Integral Plena"] = tabela.apply(
        lambda linha: (
            f"{int(linha['integrais'])} "
            f"({linha['pct_integrais']:.1f}%)"
        ).replace(".", ","),
        axis=1,
    )
    tabela["Parcial ou Mista"] = tabela.apply(
        lambda linha: (
            f"{int(linha['parciais'])} "
            f"({100 - linha['pct_integrais']:.1f}%)"
        ).replace(".", ","),
        axis=1,
    )
    return tabela.rename(
        columns={
            "ano": "Ano",
            "total_escolas": "Total de escolas",
        }
    )[
        [
            "Ano",
            "Total de escolas",
            "Integral Plena",
            "Parcial ou Mista",
        ]
    ]


def _secao_expansao(oferta):
    oferta = _recorte_anos(oferta, list(range(2016, 2026)), "oferta_anual.parquet")

    st.subheader("Evolução da proporção de escolas por tipo de oferta (2016–2025)")
    st.caption(
        "Integral Plena: escolas com 100% das matrículas do Ensino Médio em "
        "tempo integral. Parcial ou Mista: demais escolas. Os percentuais "
        "representam a proporção de escolas em cada categoria no ano."
    )
    fig = go.Figure()
    for tipo, percentuais, cor in [
        (TIPO_OFERTA_INTEGRAL, oferta["pct_integrais"], COR_INTEGRAL),
        (TIPO_OFERTA_PARCIAL, 100 - oferta["pct_integrais"], COR_PARCIAL),
    ]:
        fig.add_trace(
            go.Scatter(
                x=oferta["ano"],
                y=percentuais,
                mode="lines+markers",
                name=tipo,
                line=dict(color=cor, width=3),
                marker=dict(size=7),
                hovertemplate=(
                    f"{tipo}<br>"
                    "Ano: %{x}<br>Escolas: %{y:.1f}%<extra></extra>"
                ),
            ),
        )
    fig.update_layout(
        template="plotly_white",
        height=410,
        margin=dict(l=0, r=0, t=60, b=0),
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(2016, 2026)),
            title="Ano",
        ),
        yaxis=dict(title="Escolas (%)", ticksuffix="%", range=[0, 100]),
        showlegend=True,
        legend=dict(orientation="h", y=1.08, yanchor="bottom", x=0, xanchor="left"),
    )
    st.plotly_chart(fig, use_container_width=True)
    inicio = oferta.iloc[0]
    fim = oferta.iloc[-1]
    pico = oferta.loc[oferta["pct_integrais"].idxmax()]
    percentual = lambda valor: f"{valor:.1f}".replace(".", ",")
    st.caption(
        "A proporção de escolas classificadas como integrais na rede estadual de "
        f"ensino médio da Paraíba passou de {percentual(inicio['pct_integrais'])}% "
        f"em {int(inicio['ano'])} para {percentual(fim['pct_integrais'])}% em "
        f"{int(fim['ano'])}. O maior valor da série foi {percentual(pico['pct_integrais'])}% "
        f"em {int(pico['ano'])}."
    )
    with st.expander("Ver dados anuais da oferta (2016–2025)"):
        st.dataframe(
            _tabela_oferta_anual(oferta),
            hide_index=True,
            use_container_width=True,
        )


def _secao_ideb(ideb_oferta, testes):
    anos_ideb = ANOS_IDEB_OFERTA
    ideb_oferta = ideb_oferta.loc[
        ideb_oferta["ano"].isin(anos_ideb)
        & ideb_oferta["tipo_oferta"].isin(
            [TIPO_OFERTA_INTEGRAL, TIPO_OFERTA_PARCIAL]
        )
    ].copy()
    if set(ideb_oferta["ano"]) != set(anos_ideb):
        faltantes = sorted(set(anos_ideb) - set(ideb_oferta["ano"]))
        raise ValueError(
            "ideb_por_oferta.parquet não contém os anos esperados: "
            + ", ".join(map(str, faltantes))
        )

    st.subheader("IDEB médio por tipo de oferta")
    st.caption(
        "Médias de IDEB exportadas por tipo de oferta. O detalhamento com quantidade "
        "de escolas e cobertura está disponível no tooltip de cada ponto."
    )

    fig = go.Figure()
    for tipo, cor in [
        (TIPO_OFERTA_INTEGRAL, COR_INTEGRAL),
        (TIPO_OFERTA_PARCIAL, COR_PARCIAL),
    ]:
        serie = ideb_oferta.loc[ideb_oferta["tipo_oferta"] == tipo].sort_values("ano")
        fig.add_trace(
            go.Scatter(
                x=serie["ano"],
                y=serie["media_ideb"],
                mode="lines+markers",
                name=tipo,
                line=dict(color=cor, width=3),
                marker=dict(size=8),
                customdata=serie[["com_ideb", "total_escolas", "cobertura_pct"]],
                hovertemplate=(
                    f"{tipo}<br>Ano: %{{x}}<br>IDEB médio: %{{y:.2f}}"
                    "<br>N com IDEB: %{customdata[0]}"
                    "<br>Cobertura: %{customdata[2]:.2f}% (%{customdata[0]} de "
                    "%{customdata[1]})<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        template="plotly_white",
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(tickmode="array", tickvals=anos_ideb, title="Edição do IDEB"),
        yaxis=dict(
            title="IDEB médio",
            range=[2.5, 5.0],
            tickmode="array",
            tickvals=[2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
            ticktext=["2,5", "3,0", "3,5", "4,0", "4,5", "5,0"],
        ),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    testes = _recorte_anos(testes, anos_ideb, "testes_ideb_oferta.parquet")
    if "IC 95%" not in testes:
        testes["IC 95%"] = testes.apply(
            lambda linha: f"[{linha['ic95_inferior']}; {linha['ic95_superior']}]",
            axis=1,
        )
    tabela = testes[
        ["ano", "diferenca", "IC 95%", "n_integral", "n_parcial"]
    ].rename(
        columns={
            "ano": "Ano",
            "diferenca": "Diferença das médias",
            "n_integral": "N Integral Plena",
            "n_parcial": "N Parcial ou Mista",
        }
    ).copy()
    tabela["Diferença das médias"] = tabela["Diferença das médias"].map(
        _formatar_diferenca
    )
    tabela["IC 95%"] = tabela["IC 95%"].map(_formatar_ic95)
    tabela["p-valor"] = testes["p_valor"].map(_formatar_p_valor).to_numpy()
    tabela = tabela[
        [
            "Ano",
            "Diferença das médias",
            "IC 95%",
            "N Integral Plena",
            "N Parcial ou Mista",
            "p-valor",
        ]
    ]
    st.subheader("Diferença do IDEB médio entre os tipos de oferta")
    st.caption("Diferença das médias e resultados do teste t de Welch.")
    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
    )
    st.caption(
        "As escolas integrais plenas apresentaram IDEB médio superior nas quatro "
        "edições analisadas, com diferenças estatisticamente significativas pelo "
        "teste t de Welch (p < 0,001). As comparações não demonstram causalidade, "
        "e a composição dos grupos pode variar entre as edições."
    )
    st.caption(
        "Nota metodológica: as médias consideram apenas escolas com IDEB disponível "
        "em cada edição. O IDEB de 2021 não participa desta comparação devido à baixa "
        "cobertura e às particularidades daquela edição. IC 95% representa o intervalo "
        "de confiança da diferença entre as médias."
    )


def renderizar():
    st.header("Oferta integral plena e IDEB")
    st.caption(
        "Evolução da oferta integral plena e parcial ou mista, com comparação do IDEB. "
        "As comparações não demonstram causalidade."
    )
    _validar_arquivos_secao()
    dados = carregar_ensino_integral_ideb()
    _validar_colunas_secao(dados)
    oferta, ideb_oferta, testes = dados

    _secao_expansao(oferta)
    st.divider()
    _secao_ideb(ideb_oferta, testes)
