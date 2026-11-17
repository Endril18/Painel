from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from painel.barras_correlacoes import (
    criar_lista_correlacoes,
    formatar_coeficiente,
    formatar_p_ajustado,
)
from painel.dados import DATA_DIR


ANOS = [2017, 2019, 2023, 2025]
INDICADORES = [
    "Distorção idade-série",
    "Complexidade da gestão",
    "Esforço docente alto",
    "Formação docente adequada",
]
CAMPOS = {"ano", "indicador", "n", "correlacao", "p_ajustado"}
ARQUIVO = "correlacoes_indicadores.parquet"


def preparar_correlacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Valida os resultados exportados; nunca recalcula estatísticas."""
    ausentes = CAMPOS.difference(df.columns)
    if ausentes:
        raise ValueError(
            f"Colunas ausentes no Parquet: {', '.join(sorted(ausentes))}"
        )

    dados = df.loc[
        df["ano"].isin(ANOS) & df["indicador"].isin(INDICADORES),
        ["ano", "indicador", "n", "correlacao", "p_ajustado"],
    ].copy()
    if dados.duplicated(["ano", "indicador"]).any():
        raise ValueError("Há múltiplas linhas para o mesmo indicador e ano.")

    esperadas = pd.MultiIndex.from_product(
        [INDICADORES, ANOS], names=["indicador", "ano"]
    )
    presentes = pd.MultiIndex.from_frame(dados[["indicador", "ano"]])
    if len(dados) != len(esperadas) or not esperadas.isin(presentes).all():
        raise ValueError(
            f"São esperadas {len(esperadas)} correlações: "
            f"{len(INDICADORES)} indicadores × {len(ANOS)} edições."
        )

    dados["n"] = pd.to_numeric(dados["n"], errors="coerce")
    dados["correlacao"] = pd.to_numeric(dados["correlacao"], errors="coerce")
    dados["p_ajustado"] = pd.to_numeric(dados["p_ajustado"], errors="coerce")
    if dados[["n", "correlacao", "p_ajustado"]].isna().any().any():
        raise ValueError("Há valores não numéricos ou ausentes nos resultados.")
    if (dados["correlacao"].abs() > 1).any():
        raise ValueError("O coeficiente de correlação deve estar entre -1 e +1.")
    if (~dados["p_ajustado"].between(0, 1)).any():
        raise ValueError("Os p-valores ajustados precisam estar entre 0 e 1.")
    return dados


@st.cache_data
def carregar_correlacoes() -> pd.DataFrame:
    """Carrega o Parquet de resultados exportados."""
    return pd.read_parquet(DATA_DIR / ARQUIVO)


def _p_formatado(p: float) -> str:
    return formatar_p_ajustado(p)


def _tabela_resultados(recorte: pd.DataFrame) -> pd.DataFrame:
    tabela = recorte.rename(
        columns={
            "ano": "Ano",
            "indicador": "Indicador",
            "n": "Escolas analisadas",
            "correlacao": "Coeficiente",
            "p_ajustado": "p ajustado",
        }
    ).copy()
    tabela["Coeficiente"] = tabela["Coeficiente"].map(formatar_coeficiente)
    tabela["p ajustado"] = tabela["p ajustado"].map(formatar_p_ajustado)
    return tabela[
        [
            "Ano",
            "Indicador",
            "Escolas analisadas",
            "Coeficiente",
            "p ajustado",
        ]
    ]


def criar_mapa_correlacoes(df: pd.DataFrame) -> go.Figure:
    dados = preparar_correlacoes(df)

    def pivotar(campo):
        return dados.pivot(index="indicador", columns="ano", values=campo).reindex(
            index=INDICADORES, columns=ANOS
        )

    coef = pivotar("correlacao")
    qtd = pivotar("n")
    p_adj = pivotar("p_ajustado")

    rotulos = []
    hover = []
    for indicador in INDICADORES:
        linha_rotulos, linha_hover = [], []
        for ano in ANOS:
            valor = float(coef.loc[indicador, ano])
            p = float(p_adj.loc[indicador, ano])
            n = int(qtd.loc[indicador, ano])
            marca = "*" if p < 0.05 else ""
            linha_rotulos.append(f"{formatar_coeficiente(valor)}{marca}")
            linha_hover.append(
                f"<b>{indicador}</b><br>EDIÇÃO: {ano}"
                f"<br>Spearman: {formatar_coeficiente(valor)}"
                f"<br>Escolas: {n}"
                f"<br>p ajustado (BH): {_p_formatado(p)}"
                "<extra></extra>"
            )
        rotulos.append(linha_rotulos)
        hover.append(linha_hover)

    customdata = np.stack(
        [qtd.to_numpy(dtype=float), p_adj.to_numpy(dtype=float)], axis=-1
    )
    fig = go.Figure(
        go.Heatmap(
            z=coef.to_numpy(dtype=float),
            x=[str(ano) for ano in ANOS],
            y=INDICADORES,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale="RdBu",
            text=rotulos,
            texttemplate="%{text}",
            customdata=customdata,
            hovertext=hover,
            hovertemplate="%{hovertext}",
            colorbar=dict(title="r", len=0.7),
        )
    )
    fig.update_layout(
        height=max(410, 58 * len(INDICADORES)),
        template="plotly_white",
        margin=dict(l=5, r=5, t=10, b=15),
        xaxis_title="Edição do IDEB",
        yaxis=dict(autorange="reversed"),
    )
    return fig


def renderizar(ano: int):
    """Renderiza o bloco de correlações na página Visão geral."""
    st.subheader("Indicadores educacionais associados ao IDEB (2017–2025)")
    st.caption(
        "Associação de Spearman entre o IDEB e indicadores educacionais por edição. "
        "Os resultados representam o conjunto estadual: apenas o ano selecionado "
        "controla esta seção. Os demais filtros não alteram as correlações."
    )

    caminho = Path(DATA_DIR) / ARQUIVO
    if not caminho.exists():
        st.info(
            f"Arquivo analítico ausente: `{ARQUIVO}`. "
            "Exporte os resultados do notebook para ativar este bloco."
        )
        return

    try:
        dados = preparar_correlacoes(carregar_correlacoes())
    except Exception as erro:
        st.error(f"Não foi possível ler as correlações: {erro}")
        return

    recorte = dados.loc[dados["ano"] == ano].sort_values(
        "correlacao", key=lambda valores: valores.abs(),
        ascending=False, kind="stable",
    )
    if recorte.empty:
        st.info(
            f"Não há análise de correlação disponível para o ano selecionado ({ano}). "
            "As edições disponíveis são 2017, 2019, 2023 e 2025."
        )
    else:
        st.caption(f"Edição {ano} · Indicadores ordenados pela intensidade absoluta da correlação.")
        st.html(criar_lista_correlacoes(
            recorte.rename(columns={"indicador": "nome"}),
            mostrar_significancia=True,
        ))
    st.caption(
        "Vermelho indica associação negativa; azul, positiva. "
        "* p ajustado < 0,05 (Benjamini–Hochberg). "
        "Associação estatística não demonstra causalidade."
    )
    with st.expander("Ver resultados numéricos das correlações"):
        if recorte.empty:
            st.info(f"Não há resultados numéricos de correlação para {ano}.")
        else:
            st.dataframe(_tabela_resultados(recorte), hide_index=True, use_container_width=True)

    with st.expander("Comparar correlações entre edições (2017–2025)"):
        st.plotly_chart(criar_mapa_correlacoes(dados), use_container_width=True)
