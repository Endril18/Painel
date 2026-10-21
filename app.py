"""
Painel de escolas estaduais de Ensino Médio da Paraíba (2016-2025).

Execute com: streamlit run app.py
"""

import streamlit as st

from painel.config import INDICADORES
from painel.dados import carregar_dados
from painel.escola import renderizar as renderizar_escola
from painel.visao_geral import renderizar as renderizar_visao_geral


st.set_page_config(page_title="Ensino Médio da Paraíba", page_icon="🏫", layout="wide")

try:
    df, _ = carregar_dados()
except FileNotFoundError:
    st.error(
        "Arquivos de dados não encontrados. Coloque `escolas.parquet` e "
        "`escola_ano.parquet` na pasta `data/` ao lado do `app.py`."
    )
    st.stop()

anos = sorted(df["NU_ANO_CENSO"].unique())

st.sidebar.header("Filtros")
st.sidebar.caption("Os filtros abaixo se aplicam à aba **Visão geral**.")

ano = st.sidebar.select_slider("Ano", options=anos, value=anos[-1])
indicador_label = st.sidebar.selectbox("Indicador", list(INDICADORES.keys()))
indicador = INDICADORES[indicador_label]
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

st.title("Ensino Médio da rede estadual da Paraíba")
st.caption(
    "Escolas estaduais que ofertam Ensino Médio. Fonte: INEP (Censo Escolar, IDEB, "
    "taxas de rendimento e indicadores educacionais). "
    "A escola é classificada como integral quando 70% ou mais das matrículas do "
    "Ensino Médio são em tempo integral."
)

tab_geral, tab_escola = st.tabs(["Visão geral", "Escola"])
with tab_geral:
    renderizar_visao_geral(
        df, ano, indicador_label, indicador, tipo, gres_sel, mun_sel, busca
    )
with tab_escola:
    renderizar_escola(df, anos)
