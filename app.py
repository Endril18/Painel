import streamlit as st

from painel.dados import carregar_dados
from painel.caracteristicas_ideb import renderizar as renderizar_caracteristicas_ideb
from painel.escola import renderizar as renderizar_escola
from painel.integral_parcial import renderizar as renderizar_integral_parcial
from painel.inicio import renderizar as renderizar_inicio
from painel.visao_geral import renderizar_com_filtros as renderizar_visao_geral


st.set_page_config(page_title="Ensino Médio da Paraíba", page_icon="🏫", layout="wide")


try:
    df, escolas = carregar_dados()
except FileNotFoundError:
    st.error(
        "Arquivos de dados não encontrados. Coloque `escolas.parquet` e "
        "`escola_ano.parquet` na pasta `data/` ao lado do `app.py`."
    )
    st.stop()

anos = sorted(df["NU_ANO_CENSO"].unique())

def pagina_inicio():
    renderizar_inicio(df, paginas_navegacao, escolas)


def pagina_visao_geral():
    renderizar_visao_geral(df, anos)


def pagina_caracteristicas_ideb():
    renderizar_caracteristicas_ideb()


def pagina_escola():
    st.header("Escola")
    st.caption("Busque uma escola para consultar sua ficha, o histórico e a comparação com a rede.")
    renderizar_escola(df, anos)


def pagina_integral_parcial():
    renderizar_integral_parcial()


pagina_inicio_nav = st.Page(pagina_inicio, title="Início", url_path="inicio", default=True)
pagina_visao_geral_nav = st.Page(
    pagina_visao_geral,
    title="Indicadores educacionais e IDEB",
)
pagina_integral_parcial_nav = st.Page(
    pagina_integral_parcial,
    title="Ensino integral e IDEB",
    url_path="integral-parcial",
)
pagina_caracteristicas_ideb_nav = st.Page(
    pagina_caracteristicas_ideb,
    title="Características das escolas e IDEB",
    url_path="caracteristicas-ideb",
)
pagina_escola_nav = st.Page(pagina_escola, title="Escola", url_path="escola")

paginas_navegacao = {
    "visao_geral": pagina_visao_geral_nav,
    "integral_parcial": pagina_integral_parcial_nav,
    "caracteristicas_ideb": pagina_caracteristicas_ideb_nav,
    "escola": pagina_escola_nav,
}

pagina = st.navigation(
    [
        pagina_inicio_nav,
        pagina_visao_geral_nav,
        pagina_integral_parcial_nav,
        pagina_caracteristicas_ideb_nav,
        pagina_escola_nav,
    ],
    position="top",
)
pagina.run()

st.divider()
st.caption(
    "**Fontes e critério de oferta:** escolas estaduais que ofertam Ensino Médio. "
    "Fonte: INEP (Censo Escolar, IDEB, taxas de rendimento e indicadores educacionais). "
    "A escola é classificada como integral quando 70% ou mais das matrículas do "
    "Ensino Médio são em tempo integral."
)
