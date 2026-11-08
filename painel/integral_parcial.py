"""Página descritiva sobre oferta integral e parcial.

Os quatro arquivos usados nesta página são resultados analíticos exportados.
Este módulo apenas os apresenta: não refaz os pareamentos nem estima efeitos.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from painel.dados import DATA_DIR, carregar_ensino_integral_ideb


COR_INTEGRAL = "#1f77b4"
COR_PARCIAL = "#ff7f0e"
COR_AUMENTO = "#2ca02c"
COR_REDUCAO = "#d62728"
COR_ESTAVEL = "#7f7f7f"


ARQUIVOS_ANALITICOS = {
    "oferta_anual.parquet": {
        "ano", "total_escolas", "integrais", "parciais", "pct_integrais",
        "matriculas", "mat_integrais", "mat_parciais", "pct_mat_integrais",
    },
    "ideb_por_oferta.parquet": {
        "ano", "tipo_oferta", "total_escolas", "com_ideb", "cobertura_pct",
        "media_ideb", "cautela_2021",
    },
    "transicoes_ideb.parquet": {
        "CO_ENTIDADE", "ANO_TRANSICAO", "ANO_IDEB_ANTES", "IDEB_ANTES",
        "ANO_IDEB_DEPOIS", "IDEB_DEPOIS", "DIF_IDEB", "INTERVALO_ANOS",
    },
    "evolucao_grupos.parquet": {
        "ano", "mediana", "media", "n_escolas", "grupo",
    },
}


ARQUIVOS_SECAO = {
    "oferta_anual.parquet": {
        "ano", "pct_integrais", "pct_mat_integrais",
    },
    "ideb_por_oferta.parquet": {
        "ano", "tipo_oferta", "total_escolas", "com_ideb", "cobertura_pct",
        "media_ideb",
    },
    "testes_ideb_oferta.parquet": {
        "ano", "n_integral", "n_parcial", "diferenca", "ic95_inferior",
        "ic95_superior",
    },
    "componentes_ideb_2025.parquet": {
        "tipo_oferta", "n_escolas", "ideb", "nota_media", "rendimento",
    },
}


def _validar_arquivos():
    faltantes = [
        nome for nome in ARQUIVOS_ANALITICOS
        if not (DATA_DIR / nome).exists()
    ]
    if faltantes:
        raise FileNotFoundError(
            "Arquivos analíticos ausentes: " + ", ".join(faltantes)
        )


def _validar_colunas(dados):
    nomes = [
        "oferta_anual.parquet",
        "ideb_por_oferta.parquet",
        "transicoes_ideb.parquet",
        "evolucao_grupos.parquet",
    ]
    for nome, quadro in zip(nomes, dados):
        esperadas = ARQUIVOS_ANALITICOS[nome]
        ausentes = esperadas - set(quadro.columns)
        if ausentes:
            raise ValueError(
                f"{nome} não contém as colunas esperadas: {', '.join(sorted(ausentes))}"
            )


def _fmt_numero(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def _validar_arquivos_secao():
    faltantes = [
        nome for nome in ARQUIVOS_SECAO
        if not (DATA_DIR / nome).exists()
    ]
    if faltantes:
        raise FileNotFoundError(
            "Arquivos necessários para a seção Ensino integral e IDEB ausentes: "
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


def _recorte_anos(quadro, anos, nome):
    recorte = quadro.loc[quadro["ano"].isin(anos)].sort_values("ano").copy()
    faltantes = sorted(set(anos) - set(recorte["ano"]))
    if faltantes:
        raise ValueError(
            f"{nome} não contém os anos esperados: "
            f"{', '.join(map(str, faltantes))}"
        )
    return recorte


def _secao_expansao(oferta):
    oferta = _recorte_anos(oferta, list(range(2016, 2026)), "oferta_anual.parquet")

    st.subheader("Expansão da oferta integral (2016–2025)")
    st.caption(
        "A classificação considera integral a escola com pelo menos 70% das "
        "matrículas do Ensino Médio em tempo integral. O percentual de matrículas "
        "refere-se a todas as matrículas do Ensino Médio nessas escolas, e não "
        "necessariamente a matrículas individuais em jornada integral."
    )
    fig = go.Figure()
    for coluna, nome, cor in [
        ("pct_integrais", "Escolas classificadas como integrais", COR_INTEGRAL),
        (
            "pct_mat_integrais",
            "Matrículas em escolas classificadas como integrais",
            COR_PARCIAL,
        ),
    ]:
        fig.add_trace(
            go.Scatter(
                x=oferta["ano"],
                y=oferta[coluna],
                mode="lines+markers",
                name=nome,
                line=dict(color=cor, width=3),
                marker=dict(size=7),
                hovertemplate=f"{nome}<br>Ano: %{{x}}<br>Percentual: %{{y:.1f}}%<extra></extra>",
            )
        )
    fig.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(2016, 2026)),
            title="Ano",
        ),
        yaxis=dict(title="Percentual (%)", ticksuffix="%", rangemode="tozero"),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Interpretação: a expansão da oferta integral aparece simultaneamente na "
        "proporção de escolas e na proporção de matrículas localizadas nessas escolas."
    )


def _secao_ideb(ideb_oferta, testes):
    anos_ideb = [2017, 2019, 2023, 2025]
    ideb_oferta = ideb_oferta.loc[
        ideb_oferta["ano"].isin(anos_ideb)
        & ideb_oferta["tipo_oferta"].isin(["Integral", "Parcial"])
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
    for tipo, cor in [("Integral", COR_INTEGRAL), ("Parcial", COR_PARCIAL)]:
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
        yaxis=dict(title="IDEB médio", rangemode="tozero"),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    testes = _recorte_anos(testes, anos_ideb, "testes_ideb_oferta.parquet")
    tabela = testes[
        ["ano", "diferenca", "ic95_inferior", "ic95_superior", "n_integral", "n_parcial"]
    ].copy()
    tabela["ic95"] = tabela.apply(
        lambda linha: (
            f"[{linha['ic95_inferior']:.2f}; {linha['ic95_superior']:.2f}]"
        ),
        axis=1,
    )
    tabela = tabela.drop(columns=["ic95_inferior", "ic95_superior"]).rename(
        columns={
            "ano": "Ano",
            "diferenca": "Diferença das médias",
            "ic95": "IC 95%",
            "n_integral": "N escolas integral",
            "n_parcial": "N escolas parcial",
        }
    )
    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Diferença das médias": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.caption(
        "Diferença calculada como Integral − Parcial. Interpretação: as médias "
        "observadas foram maiores no grupo Integral nos quatro anos apresentados; "
        "essa comparação é descritiva e não demonstra causalidade."
    )


def _secao_componentes(componentes):
    st.subheader("Componentes do IDEB em 2025")
    componentes = componentes.set_index("tipo_oferta")
    tabela = pd.DataFrame(
        {
            "Indicador": ["IDEB médio", "Nota média padronizada", "Indicador de rendimento"],
            "Integral": [
                componentes.loc["Integral", "ideb"],
                componentes.loc["Integral", "nota_media"],
                componentes.loc["Integral", "rendimento"],
            ],
            "Parcial": [
                componentes.loc["Parcial", "ideb"],
                componentes.loc["Parcial", "nota_media"],
                componentes.loc["Parcial", "rendimento"],
            ],
            "Diferença (Integral − Parcial)": [
                componentes.loc["Integral", "ideb"] - componentes.loc["Parcial", "ideb"],
                componentes.loc["Integral", "nota_media"]
                - componentes.loc["Parcial", "nota_media"],
                componentes.loc["Integral", "rendimento"]
                - componentes.loc["Parcial", "rendimento"],
            ],
            "N escolas integral": componentes.loc["Integral", "n_escolas"],
            "N escolas parcial": componentes.loc["Parcial", "n_escolas"],
        }
    )
    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Integral": st.column_config.NumberColumn(format="%.2f"),
            "Parcial": st.column_config.NumberColumn(format="%.2f"),
            "Diferença (Integral − Parcial)": st.column_config.NumberColumn(format="%.2f"),
            "N escolas integral": st.column_config.NumberColumn(format="%d"),
            "N escolas parcial": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.caption(
        "Interpretação: em 2025, o grupo Integral apresenta valores médios superiores "
        "nos três indicadores. As diferenças são descritivas e não demonstram causalidade."
    )


def _secao_transicao(transicoes):
    st.subheader("IDEB antes e depois da transição")
    n_escolas = len(transicoes)
    mediana = transicoes["DIF_IDEB"].median()
    pct_aumento = (transicoes["DIF_IDEB"] > 0).mean() * 100
    c1, c2, c3 = st.columns(3)
    c1.metric("Escolas com IDEB antes e depois", n_escolas)
    c2.metric("Mudança mediana individual", f"+{_fmt_numero(mediana)} ponto")
    c3.metric("Apresentaram aumento do IDEB", f"{_fmt_numero(pct_aumento)}%")

    dist = transicoes.copy()
    dist["resultado"] = dist["DIF_IDEB"].map(
        lambda valor: "Aumento" if valor > 0 else "Redução" if valor < 0 else "Estável"
    )
    fig = go.Figure()
    for resultado, cor in [
        ("Aumento", COR_AUMENTO),
        ("Redução", COR_REDUCAO),
        ("Estável", COR_ESTAVEL),
    ]:
        valores = dist.loc[dist["resultado"] == resultado, "DIF_IDEB"]
        fig.add_trace(
            go.Histogram(
                x=valores,
                name=resultado,
                marker_color=cor,
                xbins=dict(size=0.2),
                hovertemplate="Diferença: %{x}<br>Escolas: %{y}<extra></extra>",
            )
        )
    fig.add_vline(x=0, line_dash="dash", line_color="#333", annotation_text="zero")
    fig.update_layout(
        template="plotly_white",
        height=330,
        margin=dict(l=0, r=0, t=10, b=0),
        barmode="stack",
        xaxis_title="Diferença individual no IDEB (depois − antes)",
        yaxis_title="Número de escolas",
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Verde: aumento; vermelho: redução; cinza: diferença igual a zero. "
        "O IDEB de 2021 já foi excluído da exportação."
    )
    with st.expander("Ver pares de IDEB antes e depois"):
        tabela = transicoes[
            [
                "CO_ENTIDADE", "ANO_TRANSICAO", "ANO_IDEB_ANTES", "IDEB_ANTES",
                "ANO_IDEB_DEPOIS", "IDEB_DEPOIS", "DIF_IDEB", "INTERVALO_ANOS",
            ]
        ].rename(
            columns={
                "CO_ENTIDADE": "CO_ENTIDADE",
                "ANO_TRANSICAO": "Ano da transição",
                "ANO_IDEB_ANTES": "Ano antes",
                "IDEB_ANTES": "IDEB antes",
                "ANO_IDEB_DEPOIS": "Ano depois",
                "IDEB_DEPOIS": "IDEB depois",
                "DIF_IDEB": "Diferença",
                "INTERVALO_ANOS": "Intervalo (anos)",
            }
        )
        st.dataframe(
            tabela.sort_values(["Ano da transição", "CO_ENTIDADE"]),
            hide_index=True,
            use_container_width=True,
            column_config={
                "IDEB antes": st.column_config.NumberColumn(format="%.1f"),
                "IDEB depois": st.column_config.NumberColumn(format="%.1f"),
                "Diferença": st.column_config.NumberColumn(format="%+.1f"),
            },
        )
    st.info(
        "Os intervalos entre as observações não são necessariamente iguais. "
        "O aumento observado não pode ser atribuído causalmente à transição."
    )


def _secao_grupos(evolucao_grupos):
    st.subheader("Evolução dos grupos")
    st.caption(
        "Mediana do IDEB entre as escolas com transição identificada e as parciais permanentes."
    )
    cores = {
        "Escolas com transição identificada": COR_INTEGRAL,
        "Parciais permanentes": COR_PARCIAL,
    }
    fig = go.Figure()
    for grupo in cores:
        serie = evolucao_grupos.loc[evolucao_grupos["grupo"] == grupo].sort_values("ano")
        fig.add_trace(
            go.Scatter(
                x=serie["ano"],
                y=serie["mediana"],
                mode="lines+markers",
                name=grupo,
                line=dict(color=cores[grupo], width=3),
                marker=dict(size=8),
                customdata=serie[["n_escolas", "media"]],
                hovertemplate=(
                    f"{grupo}<br>Ano: %{{x}}<br>Mediana: %{{y:.1f}}"
                    "<br>N: %{customdata[0]}<br>Média: %{customdata[1]:.2f}"
                    "<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        template="plotly_white",
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(dtick=2, title="Edição do IDEB"),
        yaxis=dict(title="Mediana do IDEB", rangemode="tozero"),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    tabela = evolucao_grupos[["ano", "grupo", "mediana", "media", "n_escolas"]].rename(
        columns={
            "ano": "Ano",
            "grupo": "Grupo",
            "mediana": "Mediana",
            "media": "Média",
            "n_escolas": "N escolas",
        }
    )
    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Mediana": st.column_config.NumberColumn(format="%.1f"),
            "Média": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.info(
        "A composição das amostras pode variar por edição, e algumas escolas do "
        "grupo de transição ainda eram parciais nos primeiros anos. As parciais "
        "permanentes não constituem um grupo de controle causal pareado."
    )
    st.caption(
        "Esta série tem população diferente da análise pareada de 160 escolas da "
        "seção anterior; as duas análises não são equivalentes."
    )


def renderizar():
    st.header("Ensino integral e IDEB")
    st.caption(
        "Expansão da oferta integral e comparação descritiva do IDEB por tipo de oferta. "
        "As comparações não demonstram causalidade."
    )
    _validar_arquivos_secao()
    dados = carregar_ensino_integral_ideb()
    _validar_colunas_secao(dados)
    oferta, ideb_oferta, testes, componentes = dados

    _secao_expansao(oferta)
    st.divider()
    _secao_ideb(ideb_oferta, testes)
    st.divider()
    _secao_componentes(componentes)
