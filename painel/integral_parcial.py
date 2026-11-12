"""Página descritiva sobre oferta integral e parcial.

Os três arquivos usados nesta página são resultados analíticos exportados.
Este módulo apenas os apresenta: não refaz os pareamentos nem estima efeitos.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from painel.config import TIPO_OFERTA_INTEGRAL, TIPO_OFERTA_PARCIAL
from painel.dados import DATA_DIR, carregar_ensino_integral_ideb


COR_INTEGRAL = "#1f77b4"
COR_PARCIAL = "#ff7f0e"


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
}


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

    st.subheader("Evolução da proporção de escolas integrais (2016–2025)")
    st.caption(
        "A classificação considera integral a escola com pelo menos 70% das "
        "matrículas do Ensino Médio em tempo integral. O percentual de matrículas "
        "refere-se a todas as matrículas do Ensino Médio nessas escolas, e não "
        "necessariamente a matrículas individuais em jornada integral."
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=oferta["ano"],
            y=oferta["pct_integrais"],
            mode="lines+markers",
            name="Escolas classificadas como integrais",
            line=dict(color=COR_INTEGRAL, width=3),
            marker=dict(size=7),
            hovertemplate=(
                "Escolas classificadas como integrais<br>"
                "Ano: %{x}<br>Percentual: %{y:.1f}%<extra></extra>"
            ),
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
        showlegend=False,
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


def _secao_ideb(ideb_oferta, testes):
    anos_ideb = [2017, 2019, 2023, 2025]
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
        f"Diferença calculada como {TIPO_OFERTA_INTEGRAL} − {TIPO_OFERTA_PARCIAL}. "
        "Interpretação: as médias "
        "observadas foram maiores no grupo Integral nos quatro anos apresentados; "
        "essa comparação é descritiva e não demonstra causalidade."
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
    oferta, ideb_oferta, testes = dados

    _secao_expansao(oferta)
    st.divider()
    _secao_ideb(ideb_oferta, testes)
