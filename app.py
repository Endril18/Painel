import streamlit as st

from painel.dados import carregar_dados
from painel.caracteristicas_ideb import renderizar as renderizar_caracteristicas_ideb
from painel.escola import renderizar as renderizar_escola
from painel.integral_parcial import renderizar as renderizar_integral_parcial
from painel.visao_geral import renderizar_com_filtros as renderizar_visao_geral


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

st.caption("Ensino Médio da rede estadual da Paraíba")


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


pagina = st.navigation(
    [
        st.Page(
            pagina_visao_geral,
            title="Indicadores educacionais e IDEB",
            default=True,
        ),
        st.Page(
            pagina_integral_parcial,
            title="Ensino integral e IDEB",
            url_path="integral-parcial",
        ),
        st.Page(
            pagina_caracteristicas_ideb,
            title="Características das escolas e IDEB",
            url_path="caracteristicas-ideb",
        ),
        st.Page(pagina_escola, title="Escola", url_path="escola"),
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
