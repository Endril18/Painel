"""Página Características e IDEB: resultados pré-calculados, sem inferência causal."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from painel.dados import DATA_DIR, carregar_caracteristicas_ideb

COR_ALTO = "#2456A6"
COR_BAIXO = "#D68A39"
COR_OFERTA = {"Integral": "#1f77b4", "Parcial": "#ff7f0e"}

ROTULOS_CORRELACAO = {
    "IS_INT": "Oferta integral",
    "TEM_EJA": "Oferta de EJA",
    "IN_BIBLIOTECA": "Biblioteca",
    "IN_BIBLIOTECA_SALA_LEITURA": "Biblioteca/sala de leitura",
    "IN_LABORATORIO_CIENCIAS": "Laboratório de ciências",
    "IN_LABORATORIO_INFORMATICA": "Laboratório de informática",
    "IN_QUADRA_ESPORTES": "Quadra esportiva",
    "IN_QUADRA_ESPORTES_COBERTA": "Quadra coberta",
    "IN_AUDITORIO": "Auditório",
    "IN_REFEITORIO": "Refeitório",
}

ROTULOS_PERFIL = {
    "TDI_MED_CAT_0": "Distorção idade-série (%)",
    "IED_ESFORCO_ALTO": "Docentes com esforço alto (%)",
    "AFD_ADEQUADA": "Formação docente adequada (%)",
    "IS_INT": "Escolas integrais (%)",
    "TEM_EJA": "Escolas com EJA (%)",
}


def _tabela_perfil(perfil):
    """Uma linha por característica, com valores e N válidos dos dois grupos."""
    chaves = ["coluna", "caracteristica", "unidade", "estatistica"]
    valores = perfil.pivot(index=chaves, columns="grupo", values="valor")
    ns = perfil.pivot(index=chaves, columns="grupo", values="n_valido")

    tabela = pd.DataFrame({
        "ID": valores.index.get_level_values("coluna"),
        "Característica": valores.index.get_level_values("caracteristica"),
        "Unidade": valores.index.get_level_values("unidade"),
        "Medida": valores.index.get_level_values("estatistica"),
        "Baixo": valores["Baixo"].to_numpy(),
        "N baixo": ns["Baixo"].to_numpy(),
        "Alto": valores["Alto"].to_numpy(),
        "N alto": ns["Alto"].to_numpy(),
    })
    tabela["Característica"] = tabela.apply(
        lambda r: ROTULOS_PERFIL.get(r["ID"], r["Característica"]), axis=1
    )
    return tabela.reset_index(drop=True)


def _perfil(perfil):
    st.subheader("Características das escolas com IDEB alto e baixo — 2025")
    st.caption(
        "Grupos definidos pelos percentis 20 e 80 da distribuição do IDEB. "
        "As escolas empatadas nos limites foram incluídas."
    )

    recortes = [r for r in ("Todas", "Só integrais", "Só parciais")
                if r in perfil["recorte"].unique()]
    recorte = st.selectbox("População da comparação", recortes, key="carac_recorte")
    dados = perfil.loc[perfil["recorte"] == recorte].copy()
    if dados.empty:
        st.info("Não há características disponíveis para esse recorte.")
        return

    p20 = float(dados["p20"].iloc[0])
    p80 = float(dados["p80"].iloc[0])
    n_baixo = int(dados.loc[dados["grupo"] == "Baixo", "n_grupo"].iloc[0])
    n_alto = int(dados.loc[dados["grupo"] == "Alto", "n_grupo"].iloc[0])
    a, b, c, d = st.columns(4)
    a.metric("Limite baixo (P20)", f"{p20:.1f}".replace(".", ","))
    b.metric("Limite alto (P80)", f"{p80:.1f}".replace(".", ","))
    c.metric("Escolas no grupo baixo", n_baixo)
    d.metric("Escolas no grupo alto", n_alto)

    tabela = _tabela_perfil(dados)
    tipo = st.radio(
        "Indicadores para o gráfico",
        ["Percentuais", "Índices (0 a 100)", "Outros indicadores"],
        horizontal=True,
        key="carac_tipo_grafico",
    )
    if tipo == "Percentuais":
        exibicao = dados.loc[dados["unidade"] == "%"].copy()
    elif tipo == "Índices (0 a 100)":
        exibicao = dados.loc[dados["coluna"].isin(
            ["IDX_INFRAESTRUTURA", "IDX_TECNOLOGIA"]
        )].copy()
    else:
        disponiveis = tabela.loc[
            (~tabela["Unidade"].eq("%")) &
            (~tabela["ID"].isin(["IDX_INFRAESTRUTURA", "IDX_TECNOLOGIA"]))
        ]
        if disponiveis.empty:
            st.info("Não há outros indicadores neste recorte.")
            exibicao = dados.iloc[:0].copy()
        else:
            opcoes = dict(zip(disponiveis["ID"], disponiveis["Característica"]))
            escolhido = st.selectbox(
                "Característica", list(opcoes), format_func=lambda v: opcoes[v],
                key="carac_outro_indicador",
            )
            exibicao = dados.loc[dados["coluna"] == escolhido].copy()

    if not exibicao.empty:
        exibicao["Rotulo"] = exibicao.apply(
            lambda r: ROTULOS_PERFIL.get(r["coluna"], r["caracteristica"]), axis=1
        )
        fig = px.bar(
            exibicao,
            x="valor", y="Rotulo", color="grupo", orientation="h",
            barmode="group", text="valor",
            color_discrete_map={"Alto": COR_ALTO, "Baixo": COR_BAIXO},
            category_orders={"grupo": ["Baixo", "Alto"]},
            custom_data=["n_valido", "n_grupo", "estatistica"],
            labels={"valor": "Valor", "Rotulo": "", "grupo": "Grupo"},
        )
        fig.update_traces(
            texttemplate="%{x:.1f}", textposition="outside", cliponaxis=False,
            hovertemplate=("%{y}<br>Grupo: %{fullData.name}<br>Valor: %{x:.2f}"
                           "<br>N válido: %{customdata[0]:.0f}"
                           "<br>N do grupo: %{customdata[1]:.0f}<extra></extra>"),
        )
        fig.update_layout(
            template="plotly_white", height=max(300, 110 * exibicao["coluna"].nunique()),
            margin=dict(l=15, r=70, t=10, b=20),
            legend=dict(orientation="h", y=1.13, x=0),
            yaxis=dict(autorange="reversed"),
        )
        if tipo == "Percentuais":
            fig.update_xaxes(title="Percentual (%)", range=[0, 110])
        elif tipo == "Índices (0 a 100)":
            fig.update_xaxes(title="Índice (0 a 100)", range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Para variáveis binárias (oferta integral e EJA), o valor é o percentual "
        "de escolas com a característica. Nas demais variáveis, é a mediana entre "
        "as escolas com informação válida. Os N podem variar por característica."
    )
    with st.expander("Ver tabela completa de características e tamanhos das amostras"):
        st.dataframe(
            tabela.drop(columns="ID").round(2),
            hide_index=True, use_container_width=True,
        )


def _dispersao(df):
    st.subheader("Distorção idade-série e IDEB — 2025")
    necessarias = {"NU_ANO_CENSO", "IDEB", "TDI_MED_CAT_0", "TIPO_OFERTA"}
    ausentes = necessarias - set(df.columns)
    if ausentes:
        st.warning("Não foi possível construir a dispersão. Colunas ausentes: "
                   + ", ".join(sorted(ausentes)))
        return
    amostra = df.loc[df["NU_ANO_CENSO"] == 2025].dropna(
        subset=["IDEB", "TDI_MED_CAT_0", "TIPO_OFERTA"]
    ).copy()
    st.caption(
        f"Cada ponto representa uma escola com os dois indicadores disponíveis "
        f"(N = {len(amostra)}). O tipo de oferta é mostrado por cor."
    )
    if amostra.empty:
        st.info("Não há dados disponíveis para a dispersão.")
        return
    hover = [c for c in ("NO_ENTIDADE", "NO_MUNICIPIO") if c in amostra]
    fig = px.scatter(
        amostra,
        x="TDI_MED_CAT_0", y="IDEB", color="TIPO_OFERTA",
        color_discrete_map=COR_OFERTA,
        hover_data=hover, opacity=0.72,
        labels={"TDI_MED_CAT_0": "Distorção idade-série (%)",
                "IDEB": "IDEB", "TIPO_OFERTA": "Oferta"},
    )
    fig.update_traces(marker=dict(size=9))
    fig.update_layout(template="plotly_white", height=440,
                      margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", y=1.14, x=0))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("O gráfico mostra associação visual, não uma relação causal.")


def _correlacoes(correlacoes):
    st.subheader("Características binárias associadas ao IDEB")
    st.caption(
        "Correlação ponto-bisserial por edição do IDEB (2017, 2019, 2023 e 2025). "
        "O IDEB de 2021 não integra esta comparação."
    )
    if correlacoes.empty:
        st.info("Não há correlações para apresentar.")
        return
    anos = [a for a in (2017, 2019, 2023, 2025)
            if a in correlacoes["ano"].unique()]
    nomes = sorted(correlacoes["variavel"].unique(),
                   key=lambda v: ROTULOS_CORRELACAO.get(v, v))
    if not anos or not nomes:
        st.info("Não há resultados disponíveis.")
        return
    c = correlacoes.copy()
    z = c.pivot(index="variavel", columns="ano", values="correlacao").reindex(
        index=nomes, columns=anos
    )
    n = c.pivot(index="variavel", columns="ano", values="n").reindex(
        index=nomes, columns=anos
    )
    padj = c.pivot(index="variavel", columns="ano", values="p_ajustado").reindex(
        index=nomes, columns=anos
    )
    notas = []
    for var in nomes:
        linha = []
        for ano in anos:
            r = z.loc[var, ano]
            p = padj.loc[var, ano]
            if pd.isna(r):
                linha.append("")
            else:
                linha.append(f"{r:.2f}" + ("*" if pd.notna(p) and p < 0.05 else ""))
        notas.append(linha)
    customdata = np.stack([n.to_numpy(dtype=float),
                           padj.to_numpy(dtype=float)], axis=-1)
    fig = go.Figure(go.Heatmap(
        z=z.to_numpy(dtype=float), x=[str(a) for a in anos],
        y=[ROTULOS_CORRELACAO.get(v, v) for v in nomes],
        zmin=-1, zmax=1, zmid=0, colorscale="RdBu", reversescale=False,
        text=notas, texttemplate="%{text}",
        customdata=customdata,
        hovertemplate=("%{y}<br>Ano: %{x}<br>Correlação: %{z:.3f}"
                       "<br>N: %{customdata[0]:.0f}"
                       "<br>p ajustado: %{customdata[1]:.3g}<extra></extra>"),
        colorbar=dict(title="r", len=0.7),
    ))
    fig.update_layout(
        height=max(390, 50 * len(nomes)),
        template="plotly_white",
        margin=dict(l=5, r=5, t=10, b=15),
        xaxis_title="Edição do IDEB", yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "* p ajustado < 0,05 (Benjamini–Hochberg, separado por edição). "
        "A ausência de um resultado não deve ser interpretada como correlação zero. "
        "Associação estatística não demonstra causalidade."
    )
    with st.expander("Ver resultados numéricos das correlações"):
        st.dataframe(c.round(4), hide_index=True, use_container_width=True)


def renderizar(df):
    st.header("Características e IDEB")
    st.write(
        "Explore as características das escolas nos extremos do IDEB de 2025 "
        "e as associações observadas nas diferentes edições do indicador."
    )
    necessarios = ("perfil_ideb_2025.parquet", "correlacoes_ideb.parquet")
    faltantes = [nome for nome in necessarios if not (DATA_DIR / nome).exists()]
    if faltantes:
        st.info(
            "Para ativar esta página, coloque na pasta `data/` os arquivos "
            "exportados do Colab: " + ", ".join(f"`{nome}`" for nome in faltantes)
        )
        return
    try:
        perfil, correlacoes = carregar_caracteristicas_ideb()
    except Exception as erro:
        st.error(f"Não foi possível ler os arquivos analíticos: {erro}")
        return

    _perfil(perfil)
    st.divider()
    _dispersao(df)
    st.divider()
    _correlacoes(correlacoes)
