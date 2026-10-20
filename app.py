"""
Painel de escolas estaduais de Ensino Médio da Paraíba (2016-2025)
Aba: Visão geral (mapa, filtros, indicadores-resumo e ranking)

Arquivos esperados na pasta data/:
  - escolas.parquet     (uma linha por escola)
  - escola_ano.parquet  (uma linha por escola e ano)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ensino Médio da Paraíba",
    page_icon="🏫",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"
REF_IDEB = 4.4  # referência exibida nos gráficos de IDEB
ANOS_IDEB = [2017, 2019, 2021, 2023, 2025]
PB_CENTRO = {"lat": -7.15, "lon": -36.75}

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


def formatar(valor, unidade=""):
    if pd.isna(valor):
        return "sem dado"
    return f"{valor:.1f}{unidade}".replace(".", ",")


try:
    df, escolas = carregar_dados()
except FileNotFoundError:
    st.error(
        "Arquivos de dados não encontrados. Coloque `escolas.parquet` e "
        "`escola_ano.parquet` na pasta `data/` ao lado do `app.py`."
    )
    st.stop()


# ----------------------------------------------------------------------------
# Filtros (barra lateral)
# ----------------------------------------------------------------------------
st.sidebar.header("Filtros")

anos = sorted(df["NU_ANO_CENSO"].unique())
ano = st.sidebar.select_slider("Ano", options=anos, value=anos[-1])

indicador_label = st.sidebar.selectbox("Indicador", list(INDICADORES.keys()))
coluna, unidade, melhor_maior, so_anos_ideb = INDICADORES[indicador_label]

tipo = st.sidebar.radio("Tipo de oferta", ["Todas", "Integral", "Parcial"], horizontal=True)

gres_disp = sorted(df["GRE"].unique(), key=lambda s: (s == "Sem GRE", int(s.split("ª")[0]) if "ª" in s else 99))
gres_sel = st.sidebar.multiselect("GRE", gres_disp, placeholder="Todas")

base_mun = df if not gres_sel else df[df["GRE"].isin(gres_sel)]
municipios_disp = sorted(base_mun["NO_MUNICIPIO"].dropna().unique())
mun_sel = st.sidebar.multiselect("Município", municipios_disp, placeholder="Todos")

busca = st.sidebar.text_input("Buscar escola pelo nome")

# aplica filtros
d = df[df["NU_ANO_CENSO"] == ano].copy()
if tipo != "Todas":
    d = d[d["TIPO_OFERTA"] == tipo]
if gres_sel:
    d = d[d["GRE"].isin(gres_sel)]
if mun_sel:
    d = d[d["NO_MUNICIPIO"].isin(mun_sel)]
if busca:
    d = d[d["NO_ENTIDADE"].str.contains(busca, case=False, na=False)]


# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------
st.title("Ensino Médio da rede estadual da Paraíba")
st.caption(
    "Escolas estaduais que ofertam Ensino Médio. Fonte: INEP (Censo Escolar, IDEB, "
    "taxas de rendimento e indicadores educacionais). "
    "A escola é classificada como integral quando 70% ou mais das matrículas do "
    "Ensino Médio são em tempo integral."
)

# Avisos sobre disponibilidade do indicador
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
    st.stop()


# ----------------------------------------------------------------------------
# Indicadores-resumo
# ----------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Escolas no filtro", f"{n_total}")
c2.metric(f"Com dado de {indicador_label.split(' (')[0]}", f"{n_com_dado}")
c3.metric(
    "Mediana do indicador",
    formatar(d_ind[coluna].median(), unidade) if n_com_dado else "sem dado",
)
if coluna == "IDEB" and n_com_dado:
    pct = (d_ind["IDEB"] >= REF_IDEB).mean() * 100
    c4.metric(f"Com IDEB ≥ {str(REF_IDEB).replace('.', ',')}", f"{pct:.0f}%".replace(".", ","))
else:
    pct_int = (d["TIPO_OFERTA"] == "Integral").mean() * 100
    c4.metric("Escolas integrais", f"{pct_int:.0f}%")


# ----------------------------------------------------------------------------
# Mapa
# ----------------------------------------------------------------------------
st.subheader("Mapa das escolas")

d_map = d.dropna(subset=["LATITUDE", "LONGITUDE"])
sem_coord = d[d["LATITUDE"].isna() | d["LONGITUDE"].isna()]

# Compatibilidade entre versões do plotly (Scattermap x Scattermapbox)
USA_MAP_NOVO = hasattr(go, "Scattermap")
ScatterMap = go.Scattermap if USA_MAP_NOVO else go.Scattermapbox


def texto_hover(r):
    linhas = [
        f"<b>{r.NO_ENTIDADE}</b>",
        f"{r.NO_MUNICIPIO} · {r.GRE}",
        f"{indicador_label}: {formatar(getattr(r, 'VALOR'), unidade)}",
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
            name="Sem dado",
        )
    )

if len(com_valor):
    if melhor_maior is True:
        escala = "RdYlGn"
    elif melhor_maior is False:
        escala = "RdYlGn_r"
    else:
        escala = "Viridis"
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
            name=indicador_label,
        )
    )

layout_mapa = dict(center=PB_CENTRO, zoom=6.6)
if USA_MAP_NOVO:
    fig.update_layout(map=dict(style="open-street-map", **layout_mapa))
else:
    fig.update_layout(mapbox=dict(style="open-street-map", **layout_mapa))
fig.update_layout(
    height=560,
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
)

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
    notas.append(f"{n_total - n_com_dado} escola(s) sem dado para este indicador em {ano} (pontos cinza).")
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


# ----------------------------------------------------------------------------
# Distribuição e ranking
# ----------------------------------------------------------------------------
if n_com_dado == 0:
    st.stop()

col_dist, col_rank = st.columns([1, 1])

with col_dist:
    st.subheader("Distribuição do indicador")
    hist = px.histogram(
        d_ind,
        x=coluna,
        nbins=20,
        color="TIPO_OFERTA",
        color_discrete_map={"Integral": "#1f77b4", "Parcial": "#ff7f0e"},
        labels={coluna: indicador_label, "TIPO_OFERTA": "Oferta", "count": "Escolas"},
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
            hide_index=True,
            use_container_width=True,
            column_config=cfg,
        )
    with aba_menor:
        st.dataframe(
            tabela_base.nsmallest(n_rank, indicador_label),
            hide_index=True,
            use_container_width=True,
            column_config=cfg,
        )
    if melhor_maior is False:
        st.caption("Neste indicador, valores menores indicam melhor situação.")
    elif melhor_maior is None:
        st.caption("Este indicador descreve o perfil da escola; maior ou menor não significa melhor ou pior.")
