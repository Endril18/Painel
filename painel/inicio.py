"""Página de apresentação do painel."""

import streamlit as st


def renderizar(df, paginas, escolas=None):
    """Renderiza a apresentação inicial e os atalhos para as análises."""
    ano_inicial = int(df["NU_ANO_CENSO"].min())
    ano_final = int(df["NU_ANO_CENSO"].max())
    base_escolas = df if escolas is None else escolas
    numero_escolas = int(base_escolas["CO_ENTIDADE"].nunique())

    st.markdown(":blue[**PAINEL INTERATIVO · PARAÍBA**]")
    st.title("Ensino Médio Estadual da Paraíba")

    st.write("")
    metricas = [
    ]
    colunas = st.columns(3, gap="medium")
    for coluna, (valor, rotulo) in zip(colunas, metricas):
        with coluna:
            with st.container(border=True):
                st.metric(label=rotulo, value=valor)

    st.subheader("Explorar")

    exploracoes = [
        (
            ":material/map:",
            "Indicadores educacionais e IDEB",
            "Veja no mapa onde estão as escolas e compare indicadores por ano, GRE e município.",
            "Explorar o mapa →",
            paginas["visao_geral"],
        ),
        (
            ":material/trending_up:",
            "Ensino integral e IDEB",
            "Acompanhe a expansão do ensino integral e compare o IDEB de escolas integrais e parciais.",
            "Ver a comparação →",
            paginas["integral_parcial"],
        ),
        (
            ":material/analytics:",
            "Características das escolas e IDEB",
            "Veja quais características das escolas estão associadas ao IDEB.",
            "Ver características →",
            paginas["caracteristicas_ideb"],
        ),
        (
            ":material/school:",
            "Escola",
            "Consulte uma escola e compare seu histórico com a GRE e a rede estadual.",
            "Consultar uma escola →",
            paginas["escola"],
        ),
    ]

    for inicio in range(0, len(exploracoes), 2):
        colunas = st.columns(2, gap="medium")
        for coluna, (icone, titulo, descricao, rotulo_link, pagina) in zip(
            colunas, exploracoes[inicio : inicio + 2]
        ):
            with coluna:
                with st.container(border=True):
                    st.subheader(f"{icone} {titulo}")
                    st.write(descricao)
                    st.page_link(
                        pagina,
                        label=rotulo_link,
                        use_container_width=True,
                    )

