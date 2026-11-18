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
CARACTERISTICAS = {
    "IN_EJA": "Oferta de EJA",
    "IN_LABORATORIO_CIENCIAS": "Laboratório de ciências",
    "IN_AUDITORIO": "Auditório",
    "IN_LABORATORIO_INFORMATICA": "Laboratório de informática",
    "IN_QUADRA_ESPORTES": "Quadra esportiva",
    "IN_REFEITORIO": "Refeitório",
    "IS_INT": "Integral Plena",
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
ARQUIVO = "correlacoes_censo_ideb.parquet"


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

    numericas = [
        "n",
        "n_com_caracteristica",
        "pct_com_caracteristica",
        "correlacao",
        "p_ajustado",
    ]
    for coluna in numericas:
        original = dados[coluna]
        dados[coluna] = pd.to_numeric(original, errors="coerce")
        if dados[coluna].isna().ne(original.isna()).any():
            raise ValueError(f"Há valores não numéricos na coluna '{coluna}'.")
    if (dados["correlacao"].dropna().abs() > 1).any():
        raise ValueError("O coeficiente de correlação deve estar entre -1 e +1.")
    if (~dados["p_ajustado"].dropna().between(0, 1)).any():
        raise ValueError("Os p-valores ajustados precisam estar entre 0 e 1.")
    if (~dados["pct_com_caracteristica"].dropna().between(0, 100)).any():
        raise ValueError("Os percentuais de características precisam estar entre 0 e 100.")
    esperadas = pd.MultiIndex.from_product(
        [CARACTERISTICAS, ANOS], names=["variavel", "ano"]
    )
    presentes = pd.MultiIndex.from_frame(dados[["variavel", "ano"]])
    if len(dados) != len(esperadas) or not esperadas.isin(presentes).all():
        raise ValueError(
            f"São esperadas {len(esperadas)} correlações: "
            f"{len(CARACTERISTICAS)} características × {len(ANOS)} edições."
        )
    return dados.sort_values(["variavel", "ano"], kind="stable").reset_index(drop=True)


def _formatar_p(valor: float) -> str:
    return formatar_p_ajustado(valor)


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
    hover = []
    for variavel in CARACTERISTICAS:
        linha, linha_hover = [], []
        for ano in ANOS:
            valor = coef.loc[variavel, ano]
            if pd.isna(valor):
                linha.append("—")
                linha_hover.append(
                    f"<b>{CARACTERISTICAS[variavel]}</b><br>Edição: {ano}"
                    "<br>Sem resultado<extra></extra>"
                )
                continue
            marca = "*" if p_adj.loc[variavel, ano] < 0.05 else ""
            coeficiente = formatar_coeficiente(valor)
            percentual = f"{pct_caracteristica.loc[variavel, ano]:.1f}%".replace(
                ".", ","
            )
            linha.append(f"{coeficiente}{marca}")
            linha_hover.append(
                f"<b>{CARACTERISTICAS[variavel]}</b><br>Edição: {ano}"
                f"<br>Ponto-bisserial: {coeficiente}"
                f"<br>Escolas analisadas: {int(qtd.loc[variavel, ano])}"
                f"<br>Com característica: {int(qtd_caracteristica.loc[variavel, ano])}"
                f"<br>Percentual: {percentual}"
                f"<br>p ajustado (BH): {_formatar_p(p_adj.loc[variavel, ano])}"
                "<extra></extra>"
            )
        rotulos.append(linha)
        hover.append(linha_hover)

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
            hovertext=hover,
            hovertemplate="%{hovertext}",
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


def _tabela_detalhes(dados: pd.DataFrame, ano: int) -> pd.DataFrame:
    detalhes = _ordenar_correlacoes(dados, ano).copy()
    detalhes["Característica"] = detalhes["variavel"].map(CARACTERISTICAS)
    detalhes["Coeficiente"] = detalhes["correlacao"].map(formatar_coeficiente)
    detalhes["% com característica"] = detalhes["pct_com_caracteristica"].map(
        lambda valor: "—" if pd.isna(valor) else f"{valor:.1f}%".replace(".", ",")
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
    ]


def _ordenar_correlacoes(dados: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Ordena a edição pela intensidade absoluta da correlação."""
    recorte = dados.loc[
        (dados["ano"] == ano) & dados["correlacao"].notna(),
        [
            "ano",
            "variavel",
            "n",
            "n_com_caracteristica",
            "pct_com_caracteristica",
            "correlacao",
            "p_ajustado",
        ],
    ].copy()

    return recorte.sort_values(
        "correlacao",
        key=lambda valores: valores.abs(),
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)


def _criar_lista_correlacoes(dados: pd.DataFrame) -> str:
    return criar_lista_correlacoes(
        dados.assign(nome=dados["variavel"].map(CARACTERISTICAS)),
        mostrar_significancia=True,
    )


def _selecionar_ano() -> int:
    controle_ano = getattr(st, "segmented_control", None)
    if controle_ano is not None:
        return int(controle_ano(
            "Ano de referência",
            options=ANOS,
            default=2025,
            format_func=str,
            key="caracteristicas_ideb_ano",
        ))
    else:
        return int(st.radio(
            "Ano de referência",
            options=ANOS,
            index=ANOS.index(2025),
            format_func=str,
            horizontal=True,
            key="caracteristicas_ideb_ano",
        ))


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

    st.subheader("Características escolares associadas ao IDEB (2017–2025)")
    st.caption(
        "Associação ponto-bisserial entre o IDEB e características escolares binárias "
        "por edição. Os resultados representam o conjunto estadual; os demais filtros "
        "não alteram as correlações."
    )

    ano = _selecionar_ano()
    recorte = _ordenar_correlacoes(dados, ano)
    if recorte.empty:
        st.info("Não há coeficientes disponíveis para a edição selecionada.")
    else:
        st.caption(
            f"Edição {ano} · Características ordenadas pela intensidade absoluta "
            "da correlação."
        )
        st.html(_criar_lista_correlacoes(recorte))
    st.caption(
        "Vermelho indica associação negativa; azul, positiva. "
        "* p ajustado < 0,05 (Benjamini–Hochberg). "
        "Associação estatística não demonstra causalidade."
    )

    with st.expander("Ver resultados numéricos das correlações"):
        if recorte.empty:
            st.info(f"Não há resultados numéricos de correlação para {ano}.")
        else:
            st.dataframe(
                _tabela_detalhes(dados, ano),
                hide_index=True,
                use_container_width=True,
            )

    with st.expander("Comparar correlações entre edições (2017–2025)"):
        st.plotly_chart(_criar_heatmap(dados), use_container_width=True)
