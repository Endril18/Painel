"""Características das escolas associadas ao IDEB.

Este módulo apenas apresenta resultados estatísticos já exportados. As
correlações e os p-valores ajustados não são recalculados no Streamlit.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from painel.dados import DATA_DIR


ANOS = [2017, 2019, 2023, 2025]
CARACTERISTICAS = {
    "IN_EJA": "Oferta de EJA",
    "IN_LABORATORIO_CIENCIAS": "Laboratório de ciências",
    "IN_AUDITORIO": "Auditório",
    "IN_LABORATORIO_INFORMATICA": "Laboratório de informática",
    "IN_QUADRA_ESPORTES": "Quadra esportiva",
}
CAMPOS_OBRIGATORIOS = {
    "ano",
    "variavel",
    "n",
    "n_com_caracteristica",
    "pct_com_caracteristica",
    "correlacao",
    "p_ajustado",
}
ARQUIVO = "correlacoes_ideb.parquet"


@st.cache_data
def carregar_caracteristicas_ideb() -> pd.DataFrame:
    """Carrega os resultados exportados para esta página.

    O carregamento fica local ao módulo para que a página continue compatível
    com versões anteriores de ``painel.dados`` durante um deploy incremental.
    """
    return pd.read_parquet(DATA_DIR / ARQUIVO)


def preparar_correlacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e seleciona os resultados exportados, sem recalculá-los."""
    ausentes = CAMPOS_OBRIGATORIOS.difference(df.columns)
    if ausentes:
        raise ValueError(
            "Colunas ausentes no Parquet: " + ", ".join(sorted(ausentes))
        )

    dados = df.loc[
        df["ano"].isin(ANOS) & df["variavel"].isin(CARACTERISTICAS),
        sorted(CAMPOS_OBRIGATORIOS),
    ].copy()
    if dados.duplicated(["ano", "variavel"]).any():
        raise ValueError("Há múltiplas linhas para a mesma característica e ano.")

    esperadas = pd.MultiIndex.from_product(
        [CARACTERISTICAS, ANOS], names=["variavel", "ano"]
    )
    presentes = pd.MultiIndex.from_frame(dados[["variavel", "ano"]])
    if len(dados) != len(esperadas) or not esperadas.isin(presentes).all():
        raise ValueError("São esperadas 20 correlações: 5 características × 4 edições.")

    numericas = [
        "n",
        "n_com_caracteristica",
        "pct_com_caracteristica",
        "correlacao",
        "p_ajustado",
    ]
    for coluna in numericas:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    if dados[numericas].isna().any().any():
        raise ValueError("Há valores não numéricos ou ausentes nos resultados.")
    if (dados["correlacao"].abs() > 1).any():
        raise ValueError("O coeficiente de correlação deve estar entre -1 e +1.")
    if (~dados["p_ajustado"].between(0, 1)).any():
        raise ValueError("Os p-valores ajustados precisam estar entre 0 e 1.")
    if (~dados["pct_com_caracteristica"].between(0, 100)).any():
        raise ValueError("Os percentuais de características precisam estar entre 0 e 100.")
    return dados.sort_values(["variavel", "ano"], kind="stable").reset_index(drop=True)


def _formatar_p(valor: float) -> str:
    return "< 0,001" if valor < 0.001 else f"{valor:.3f}".replace(".", ",")


def _criar_heatmap(dados: pd.DataFrame) -> go.Figure:
    coef = dados.pivot(index="variavel", columns="ano", values="correlacao").reindex(
        index=list(CARACTERISTICAS), columns=ANOS
    )
    qtd = dados.pivot(index="variavel", columns="ano", values="n").reindex(
        index=list(CARACTERISTICAS), columns=ANOS
    )
    qtd_caracteristica = dados.pivot(
        index="variavel", columns="ano", values="n_com_caracteristica"
    ).reindex(index=list(CARACTERISTICAS), columns=ANOS)
    pct_caracteristica = dados.pivot(
        index="variavel", columns="ano", values="pct_com_caracteristica"
    ).reindex(index=list(CARACTERISTICAS), columns=ANOS)
    p_adj = dados.pivot(index="variavel", columns="ano", values="p_ajustado").reindex(
        index=list(CARACTERISTICAS), columns=ANOS
    )

    rotulos = []
    for variavel in CARACTERISTICAS:
        linha = []
        for ano in ANOS:
            valor = float(coef.loc[variavel, ano])
            marca = "*" if p_adj.loc[variavel, ano] < 0.05 else ""
            linha.append(f"{valor:.3f}{marca}".replace(".", ","))
        rotulos.append(linha)

    customdata = np.stack(
        [
            qtd.to_numpy(dtype=float),
            qtd_caracteristica.to_numpy(dtype=float),
            pct_caracteristica.to_numpy(dtype=float),
            p_adj.to_numpy(dtype=float),
        ],
        axis=-1,
    )
    fig = go.Figure(
        go.Heatmap(
            z=coef.to_numpy(dtype=float),
            x=[str(ano) for ano in ANOS],
            y=list(CARACTERISTICAS.values()),
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale="RdBu",
            text=rotulos,
            texttemplate="%{text}",
            customdata=customdata,
            hovertemplate=(
                "%{y}<br>Edição: %{x}"
                "<br>Ponto-bisserial: %{z:.3f}"
                "<br>Escolas analisadas: %{customdata[0]:.0f}"
                "<br>Com característica: %{customdata[1]:.0f}"
                "<br>Percentual: %{customdata[2]:.1f}%"
                "<br>p ajustado (BH): %{customdata[3]:.3g}<extra></extra>"
            ),
            colorbar=dict(title="r", len=0.7),
        )
    )
    fig.update_layout(
        height=max(410, 58 * len(CARACTERISTICAS)),
        template="plotly_white",
        margin=dict(l=5, r=5, t=10, b=15),
        xaxis_title="Edição do IDEB",
        yaxis=dict(autorange="reversed"),
    )
    return fig


def _tabela_detalhes(dados: pd.DataFrame) -> pd.DataFrame:
    detalhes = dados.copy()
    detalhes["Característica"] = detalhes["variavel"].map(CARACTERISTICAS)
    detalhes["Coeficiente"] = detalhes["correlacao"].map(
        lambda valor: f"{valor:.3f}".replace(".", ",")
    )
    detalhes["% com característica"] = detalhes["pct_com_caracteristica"].map(
        lambda valor: f"{valor:.1f}%".replace(".", ",")
    )
    detalhes["p ajustado"] = detalhes["p_ajustado"].map(_formatar_p)
    return detalhes.rename(
        columns={
            "ano": "Ano",
            "n": "Escolas analisadas",
            "n_com_caracteristica": "Escolas com característica",
        }
    )[
        [
            "Ano",
            "Característica",
            "Coeficiente",
            "Escolas analisadas",
            "Escolas com característica",
            "% com característica",
            "p ajustado",
        ]
    ].sort_values(["Característica", "Ano"], kind="stable")


def _interpretacao():
    st.markdown("**Resumo**")
    st.write(
        "A oferta de EJA apresentou associação negativa com o IDEB nas quatro "
        "edições. Laboratórios de ciências, laboratórios de informática, auditórios "
        "e quadras esportivas apresentaram associações positivas, geralmente de "
        "pequena magnitude. A direção foi consistente ao longo das edições, mas "
        "nem todas as associações foram estatisticamente significativas."
    )
    st.caption(
        "Essas correlações descrevem associações estaduais históricas e não demonstram "
        "que uma característica cause aumento ou redução do IDEB."
    )


def renderizar():
    """Renderiza a terceira seção do painel."""
    st.header("Características das escolas e IDEB")
    st.caption(
        "Associação entre características do Censo Escolar e o IDEB nas escolas "
        "estaduais de ensino médio da Paraíba."
    )
    caminho = Path(DATA_DIR) / ARQUIVO
    if not caminho.exists():
        st.info(
            f"Arquivo analítico ausente: `{ARQUIVO}`. "
            "Coloque o resultado exportado na pasta `data/` para ativar esta seção."
        )
        return

    try:
        dados = preparar_correlacoes(carregar_caracteristicas_ideb())
    except Exception as erro:
        st.error(f"Não foi possível ler as correlações: {erro}")
        return

    st.subheader(
        "Características do Censo Escolar associadas ao IDEB "
        "(2017, 2019, 2023 e 2025)"
    )
    st.plotly_chart(_criar_heatmap(dados), use_container_width=True)
    st.caption(
        "Vermelho indica associação negativa; azul, positiva; tons neutros indicam "
        "valores próximos de zero. Coeficientes positivos indicam associação com "
        "IDEB maior nas escolas que possuem a característica; negativos, com IDEB "
        "menor. * p-valor ajustado < 0,05 (Benjamini–Hochberg)."
    )

    _interpretacao()

    with st.expander("Ver detalhes estatísticos"):
        st.dataframe(
            _tabela_detalhes(dados),
            hide_index=True,
            use_container_width=True,
        )
