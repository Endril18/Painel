"""
Painel de escolas estaduais de Ensino Médio da Paraíba (2016-2025)
Abas: Visão geral (mapa, ranking) e Escola (ficha, histórico e comparação)

Arquivos esperados na pasta data/:
  - escolas.parquet     (uma linha por escola)
  - escola_ano.parquet  (uma linha por escola e ano)
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Ensino Médio da Paraíba", page_icon="🏫", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
REF_IDEB = 4.4  # referência exibida nos gráficos de IDEB
ANOS_IDEB = [2017, 2019, 2021, 2023, 2025]
PB_CENTRO = {"lat": -7.15, "lon": -36.75}
COR_ESCOLA = "#1f77b4"
COR_GRE = "#ff7f0e"
COR_REDE = "#7f7f7f"

# label -> (coluna, unidade, melhor_quando_maior, so_em_anos_ideb)
# melhor_quando_maior: True = maior é melhor, False = menor é melhor, None = neutro
INDICADORES = {
    "IDEB": ("IDEB", "", True, True),
    "Nota média padronizada (Saeb)": ("NOTA_MEDIA", "", True, True),
    "Nota de Matemática (Saeb)": ("NOTA_MAT", "", True, True),
    "Nota de Português (Saeb)": ("NOTA_PORT", "", True, True),
    "Indicador de rendimento (fluxo)": ("REND", "", True, True),
    "Taxa de aprovação (%)": ("TX_APROV_MED", "%", True, False),
    "Taxa de reprovação (%)": ("TX_REPROV_MED", "%", False, False),
    "Taxa de abandono (%)": ("TX_ABAND_MED", "%", False, False),
    "Distorção idade-série (%)": ("TDI_MED_CAT_0", "%", False, False),
    "Docentes com formação adequada (%)": ("AFD_ADEQUADA", "%", True, False),
    "Docentes com esforço alto (%)": ("IED_ESFORCO_ALTO", "%", False, False),
    "Complexidade da gestão (nível)": ("ICG_NIVEL", "", None, False),
    "Nota de infraestrutura (0-100)": ("IDX_INFRAESTRUTURA", "", True, False),
    "Nota de tecnologia (0-100)": ("IDX_TECNOLOGIA", "", True, False),
}

# Compatibilidade entre versões do plotly (Scattermap x Scattermapbox)
USA_MAP_NOVO = hasattr(go, "Scattermap")
ScatterMap = go.Scattermap if USA_MAP_NOVO else go.Scattermapbox


def aplicar_layout_mapa(fig, centro, zoom, altura):
    cfg = dict(style="open-street-map", center=centro, zoom=zoom)
    if USA_MAP_NOVO:
        fig.update_layout(map=cfg)
    else:
        fig.update_layout(mapbox=cfg)
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    escolas = pd.read_parquet(DATA_DIR / "escolas.parquet")
    escola_ano = pd.read_parquet(DATA_DIR / "escola_ano.parquet")
    df = escola_ano.merge(escolas, on="CO_ENTIDADE", how="left", validate="m:1")
    df["GRE"] = df["CO_ORGAO_REGIONAL"].apply(
        lambda x: f"{int(x)}ª GRE" if pd.notna(x) else "Sem GRE"
    )
    return df, escolas


def formatar(valor, unidade="", casas=1):
    if pd.isna(valor):
        return "sem dado"
    return f"{valor:.{casas}f}{unidade}".replace(".", ",")


try:
    df, escolas = carregar_dados()
except FileNotFoundError:
    st.error(
        "Arquivos de dados não encontrados. Coloque `escolas.parquet` e "
        "`escola_ano.parquet` na pasta `data/` ao lado do `app.py`."
    )
    st.stop()

anos = sorted(df["NU_ANO_CENSO"].unique())


# ----------------------------------------------------------------------------
# Filtros (barra lateral) - valem para a aba Visão geral
# ----------------------------------------------------------------------------
st.sidebar.header("Filtros")
st.sidebar.caption("Os filtros abaixo se aplicam à aba **Visão geral**.")

ano = st.sidebar.select_slider("Ano", options=anos, value=anos[-1])

indicador_label = st.sidebar.selectbox("Indicador", list(INDICADORES.keys()))
coluna, unidade, melhor_maior, so_anos_ideb = INDICADORES[indicador_label]

tipo = st.sidebar.radio("Tipo de oferta", ["Todas", "Integral", "Parcial"], horizontal=True)

gres_disp = sorted(
    df["GRE"].unique(),
    key=lambda s: (s == "Sem GRE", int(s.split("ª")[0]) if "ª" in s else 99),
)
gres_sel = st.sidebar.multiselect("GRE", gres_disp, placeholder="Todas")

base_mun = df if not gres_sel else df[df["GRE"].isin(gres_sel)]
municipios_disp = sorted(base_mun["NO_MUNICIPIO"].dropna().unique())
mun_sel = st.sidebar.multiselect("Município", municipios_disp, placeholder="Todos")

busca = st.sidebar.text_input("Buscar escola pelo nome")


# ----------------------------------------------------------------------------
# Aba 1: Visão geral
# ----------------------------------------------------------------------------
def aba_visao_geral():
    d = df[df["NU_ANO_CENSO"] == ano].copy()
    if tipo != "Todas":
        d = d[d["TIPO_OFERTA"] == tipo]
    if gres_sel:
        d = d[d["GRE"].isin(gres_sel)]
    if mun_sel:
        d = d[d["NO_MUNICIPIO"].isin(mun_sel)]
    if busca:
        d = d[d["NO_ENTIDADE"].str.contains(busca, case=False, na=False)]

    if so_anos_ideb and ano not in ANOS_IDEB:
        st.info(
            f"O **{indicador_label}** só existe nos anos de aplicação do IDEB "
            f"({', '.join(map(str, ANOS_IDEB))}). Em {ano} não há dado; "
            "escolha um desses anos ou outro indicador."
        )
    if so_anos_ideb and ano == 2021:
        st.warning(
            "Em 2021 a cobertura do IDEB é baixa (efeitos da pandemia). "
            "Evite interpretar este ano isoladamente."
        )

    d_ind = d.dropna(subset=[coluna])
    n_total = len(d)
    n_com_dado = len(d_ind)

    if n_total == 0:
        st.warning("Nenhuma escola encontrada com os filtros selecionados.")
        return

    # Indicadores-resumo
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Escolas no filtro", f"{n_total}")
    c2.metric(f"Com dado de {indicador_label.split(' (')[0]}", f"{n_com_dado}")
    c3.metric(
        "Mediana do indicador",
        formatar(d_ind[coluna].median(), unidade) if n_com_dado else "sem dado",
    )
    if coluna == "IDEB" and n_com_dado:
        pct = (d_ind["IDEB"] >= REF_IDEB).mean() * 100
        c4.metric(f"Com IDEB ≥ {str(REF_IDEB).replace('.', ',')}", f"{pct:.0f}%")
    else:
        c4.metric("Escolas integrais", f"{(d['TIPO_OFERTA'] == 'Integral').mean() * 100:.0f}%")

    # Mapa
    st.subheader("Mapa das escolas")
    d_map = d.dropna(subset=["LATITUDE", "LONGITUDE"])
    sem_coord = d[d["LATITUDE"].isna() | d["LONGITUDE"].isna()]

    def texto_hover(r):
        linhas = [
            f"<b>{r.NO_ENTIDADE}</b>",
            f"{r.NO_MUNICIPIO} · {r.GRE}",
            f"{indicador_label}: {formatar(r.VALOR, unidade)}",
            f"Oferta: {r.TIPO_OFERTA}",
        ]
        if r.COORD_APROX == 1:
            linhas.append("<i>Localização aproximada</i>")
        return "<br>".join(linhas)

    d_map = d_map.assign(VALOR=d_map[coluna])
    d_map["HOVER"] = [texto_hover(r) for r in d_map.itertuples()]

    fig = go.Figure()
    sem_valor = d_map[d_map["VALOR"].isna()]
    com_valor = d_map[d_map["VALOR"].notna()]

    if len(sem_valor):
        fig.add_trace(
            ScatterMap(
                lat=sem_valor["LATITUDE"],
                lon=sem_valor["LONGITUDE"],
                mode="markers",
                marker=dict(size=8, color="#9e9e9e", opacity=0.7),
                text=sem_valor["HOVER"],
                hoverinfo="text",
            )
        )
    if len(com_valor):
        escala = {True: "RdYlGn", False: "RdYlGn_r", None: "Viridis"}[melhor_maior]
        fig.add_trace(
            ScatterMap(
                lat=com_valor["LATITUDE"],
                lon=com_valor["LONGITUDE"],
                mode="markers",
                marker=dict(
                    size=10,
                    color=com_valor["VALOR"],
                    colorscale=escala,
                    showscale=True,
                    colorbar=dict(title=indicador_label.split(" (")[0], len=0.7),
                    opacity=0.9,
                ),
                text=com_valor["HOVER"],
                hoverinfo="text",
            )
        )
    aplicar_layout_mapa(fig, PB_CENTRO, 6.6, 560)
    st.plotly_chart(fig, use_container_width=True)

    notas = []
    if (d_map["COORD_APROX"] == 1).any():
        notas.append(
            f"{int((d_map['COORD_APROX'] == 1).sum())} escola(s) com localização aproximada "
            "(dividem o mesmo ponto com outra escola do município)."
        )
    if len(sem_coord):
        notas.append(f"{len(sem_coord)} escola(s) sem localização no mapa.")
    if n_com_dado < n_total:
        notas.append(
            f"{n_total - n_com_dado} escola(s) sem dado para este indicador em {ano} (pontos cinza)."
        )
    if notas:
        st.caption(" ".join(notas))

    if len(sem_coord):
        with st.expander("Escolas sem localização no mapa"):
            st.dataframe(
                sem_coord[["NO_ENTIDADE", "NO_MUNICIPIO", "GRE"]].rename(
                    columns={"NO_ENTIDADE": "Escola", "NO_MUNICIPIO": "Município"}
                ),
                hide_index=True,
                use_container_width=True,
            )

    if n_com_dado == 0:
        return

    # Distribuição e ranking
    col_dist, col_rank = st.columns(2)

    with col_dist:
        st.subheader("Distribuição do indicador")
        hist = px.histogram(
            d_ind,
            x=coluna,
            nbins=20,
            color="TIPO_OFERTA",
            color_discrete_map={"Integral": "#1f77b4", "Parcial": "#ff7f0e"},
            labels={coluna: indicador_label, "TIPO_OFERTA": "Oferta"},
            barmode="overlay",
            opacity=0.65,
        )
        hist.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Escolas")
        if coluna == "IDEB":
            hist.add_vline(
                x=REF_IDEB,
                line_dash="dash",
                line_color="#555",
                annotation_text=f"Referência {str(REF_IDEB).replace('.', ',')}",
                annotation_position="top",
            )
        st.plotly_chart(hist, use_container_width=True)

    with col_rank:
        st.subheader("Ranking")
        n_rank = min(10, n_com_dado)
        tabela_base = d_ind[["NO_ENTIDADE", "NO_MUNICIPIO", "GRE", "TIPO_OFERTA", coluna]].rename(
            columns={
                "NO_ENTIDADE": "Escola",
                "NO_MUNICIPIO": "Município",
                "TIPO_OFERTA": "Oferta",
                coluna: indicador_label,
            }
        )
        aba_maior, aba_menor = st.tabs([f"{n_rank} maiores valores", f"{n_rank} menores valores"])
        cfg = {indicador_label: st.column_config.NumberColumn(format="%.2f")}
        with aba_maior:
            st.dataframe(
                tabela_base.nlargest(n_rank, indicador_label),
                hide_index=True, use_container_width=True, column_config=cfg,
            )
        with aba_menor:
            st.dataframe(
                tabela_base.nsmallest(n_rank, indicador_label),
                hide_index=True, use_container_width=True, column_config=cfg,
            )
        if melhor_maior is False:
            st.caption("Neste indicador, valores menores indicam melhor situação.")
        elif melhor_maior is None:
            st.caption(
                "Este indicador descreve o perfil da escola; "
                "maior ou menor não significa melhor ou pior."
            )


# ----------------------------------------------------------------------------
# Aba 2: Escola
# ----------------------------------------------------------------------------
FICHA = [
    # (rótulo, coluna, unidade, casas)
    ("Matrículas no Ensino Médio", "QT_MAT_MED", "", 0),
    ("Turmas", "QT_TUR_MED", "", 0),
    ("Docentes", "QT_DOC_MED", "", 0),
    ("Alunos por turma", "ALUNOS_POR_TURMA", "", 1),
    ("Alunos por docente", "ALUNOS_POR_DOCENTE", "", 1),
    ("Matrículas em tempo integral", "PCT_INT", "%", 0),
    ("Computadores por 100 alunos", "COMPUTADORES_ALUNO_P100", "", 1),
    ("Salas climatizadas", "PCT_SALAS_CLIMATIZADAS", "%", 0),
    ("Nota de infraestrutura (0-100)", "IDX_INFRAESTRUTURA", "", 0),
    ("Nota de tecnologia (0-100)", "IDX_TECNOLOGIA", "", 0),
]

COMPARACAO = [
    "IDEB",
    "Taxa de aprovação (%)",
    "Taxa de reprovação (%)",
    "Taxa de abandono (%)",
    "Distorção idade-série (%)",
    "Docentes com formação adequada (%)",
    "Docentes com esforço alto (%)",
    "Complexidade da gestão (nível)",
    "Nota de infraestrutura (0-100)",
    "Nota de tecnologia (0-100)",
]

LOCALIZACAO = {1: "Urbana", 2: "Rural"}


def aba_escola():
    ultimo = df.sort_values("NU_ANO_CENSO").groupby("CO_ENTIDADE").tail(1)
    ano_max = max(anos)
    rotulos = {}
    for r in ultimo.itertuples():
        rot = f"{r.NO_ENTIDADE} — {r.NO_MUNICIPIO}"
        if r.NU_ANO_CENSO < ano_max:
            rot += f" (dados até {r.NU_ANO_CENSO})"
        rotulos[r.CO_ENTIDADE] = rot
    codigos = sorted(rotulos, key=lambda c: rotulos[c])

    cod = st.selectbox(
        "Escolha a escola (digite para buscar)",
        codigos,
        format_func=lambda c: rotulos[c],
        index=None,
        placeholder="Nome da escola ou município",
    )
    if cod is None:
        st.info("Selecione uma escola para ver a ficha, o histórico e a comparação com a rede.")
        return

    hist = df[df["CO_ENTIDADE"] == cod].sort_values("NU_ANO_CENSO")
    esc = hist.iloc[-1]
    gre = esc["GRE"]

    # Cabeçalho
    st.header(esc["NO_ENTIDADE"])
    loc = LOCALIZACAO.get(int(esc["TP_LOCALIZACAO"]), "") if pd.notna(esc["TP_LOCALIZACAO"]) else ""
    st.markdown(
        f"**{esc['NO_MUNICIPIO']}** · {gre}" + (f" · Zona {loc.lower()}" if loc else "")
        + f" · {esc['TIPO_OFERTA']}"
    )
    anos_escola = sorted(hist["NU_ANO_CENSO"].unique())
    if anos_escola[-1] < ano_max:
        st.warning(
            f"Esta escola não aparece no Censo mais recente. "
            f"Dados disponíveis de {anos_escola[0]} a {anos_escola[-1]}."
        )

    # Ficha e localização
    col_ficha, col_mapa = st.columns([3, 2])

    with col_ficha:
        ano_f = st.selectbox("Ano da ficha", anos_escola, index=len(anos_escola) - 1, key="ano_ficha")
        linha = hist[hist["NU_ANO_CENSO"] == ano_f].iloc[0]
        ref_ano = df[df["NU_ANO_CENSO"] == ano_f]
        st.caption(f"Em cada item, a mediana da rede estadual em {ano_f} aparece abaixo do valor.")
        cols = st.columns(5)
        for i, (rot, col, un, casas) in enumerate(FICHA):
            with cols[i % 5]:
                st.metric(rot, formatar(linha[col], un, casas))
                st.caption(f"Rede: {formatar(ref_ano[col].median(), un, casas)}")
        extra = []
        extra.append("Oferece EJA no Ensino Médio" if linha["TEM_EJA"] == 1 else "Sem EJA no Ensino Médio")
        st.caption(" · ".join(extra))

    with col_mapa:
        if pd.notna(esc["LATITUDE"]) and pd.notna(esc["LONGITUDE"]):
            fm = go.Figure(
                ScatterMap(
                    lat=[esc["LATITUDE"]], lon=[esc["LONGITUDE"]], mode="markers",
                    marker=dict(size=14, color=COR_ESCOLA),
                    text=[esc["NO_ENTIDADE"]], hoverinfo="text",
                )
            )
            aplicar_layout_mapa(fm, {"lat": esc["LATITUDE"], "lon": esc["LONGITUDE"]}, 12, 300)
            st.plotly_chart(fm, use_container_width=True)
            if esc["COORD_APROX"] == 1:
                st.caption("Localização aproximada (referência do município).")
        else:
            st.info("Esta escola não tem localização no mapa.")

    # Histórico
    st.subheader("Histórico (2016–2025)")
    ind_label = st.selectbox("Indicador", list(INDICADORES.keys()), key="ind_hist")
    ind_col, ind_un, _, ind_ideb = INDICADORES[ind_label]

    serie_escola = hist.set_index("NU_ANO_CENSO")[ind_col].reindex(anos)
    serie_rede = df.groupby("NU_ANO_CENSO")[ind_col].median().reindex(anos)
    serie_gre = df[df["GRE"] == gre].groupby("NU_ANO_CENSO")[ind_col].median().reindex(anos)

    fh = go.Figure()
    for nome, serie, cor, dash in [
        (esc["NO_ENTIDADE"], serie_escola, COR_ESCOLA, "solid"),
        (f"Mediana da {gre}", serie_gre, COR_GRE, "dash"),
        ("Mediana da rede estadual", serie_rede, COR_REDE, "dot"),
    ]:
        fh.add_trace(
            go.Scatter(
                x=anos, y=serie.values, mode="lines+markers", name=nome,
                line=dict(color=cor, dash=dash, width=3 if cor == COR_ESCOLA else 2),
                connectgaps=True,
            )
        )
    if ind_col == "IDEB":
        fh.add_hline(y=REF_IDEB, line_dash="dot", line_color="#999",
                     annotation_text=f"Referência {str(REF_IDEB).replace('.', ',')}")
    fh.update_layout(
        height=380, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(dtick=1, title=None), yaxis_title=ind_label,
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fh, use_container_width=True)
    if serie_escola.notna().sum() == 0:
        st.caption("A escola não tem dado deste indicador em nenhum ano.")
    elif ind_ideb:
        st.caption(
            "Este indicador só existe nos anos de aplicação do IDEB "
            "(2017, 2019, 2021, 2023, 2025); as linhas ligam os anos com dado. "
            "A cobertura de 2021 é baixa."
        )

    # Comparação com a GRE e a rede
    st.subheader(f"Comparação em {ano_f}")
    ref_gre = ref_ano[ref_ano["GRE"] == gre]
    linhas = []
    for rot in COMPARACAO:
        col, un, _, _ = INDICADORES[rot]
        linhas.append(
            {
                "Indicador": rot,
                "Escola": linha[col],
                f"Mediana da {gre}": ref_gre[col].median(),
                "Mediana da rede": ref_ano[col].median(),
            }
        )
    comp = pd.DataFrame(linhas)
    st.dataframe(
        comp.style.format(
            {c: (lambda v: "sem dado" if pd.isna(v) else f"{v:.1f}".replace(".", ","))
             for c in comp.columns[1:]}
        ),
        hide_index=True, use_container_width=True,
    )
    st.caption(
        f"Medianas calculadas entre as escolas estaduais com dado no ano ({len(ref_gre)} escolas na {gre}, "
        f"{len(ref_ano)} na rede). Para taxas de reprovação, abandono, distorção idade-série e esforço "
        "docente, valores menores indicam melhor situação."
    )

    # Taxas de rendimento da escola
    st.subheader("Taxas de rendimento da escola")
    tx = hist[["NU_ANO_CENSO", "TX_APROV_MED", "TX_REPROV_MED", "TX_ABAND_MED"]].melt(
        id_vars="NU_ANO_CENSO", var_name="Taxa", value_name="Percentual"
    )
    tx["Taxa"] = tx["Taxa"].map(
        {"TX_APROV_MED": "Aprovação", "TX_REPROV_MED": "Reprovação", "TX_ABAND_MED": "Abandono"}
    )
    ft = px.line(
        tx, x="NU_ANO_CENSO", y="Percentual", color="Taxa", markers=True,
        color_discrete_map={"Aprovação": "#2ca02c", "Reprovação": "#d62728", "Abandono": "#9467bd"},
        labels={"NU_ANO_CENSO": ""},
    )
    ft.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                     xaxis=dict(dtick=1), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(ft, use_container_width=True)


# ----------------------------------------------------------------------------
# Página
# ----------------------------------------------------------------------------
st.title("Ensino Médio da rede estadual da Paraíba")
st.caption(
    "Escolas estaduais que ofertam Ensino Médio. Fonte: INEP (Censo Escolar, IDEB, "
    "taxas de rendimento e indicadores educacionais). "
    "A escola é classificada como integral quando 70% ou mais das matrículas do "
    "Ensino Médio são em tempo integral."
)

tab_geral, tab_escola = st.tabs(["Visão geral", "Escola"])
with tab_geral:
    aba_visao_geral()
with tab_escola:
    aba_escola()