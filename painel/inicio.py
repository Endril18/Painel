import streamlit as st


def renderizar(df, paginas, escolas=None):
    """Renderiza a apresentação inicial e os atalhos para as análises."""
    st.title("Ensino Médio Estadual da Paraíba")
    st.caption(
        "Dados e indicadores das escolas estaduais de Ensino Médio da Paraíba, de "
        "2016 a 2025, com análises relacionadas ao IDEB."
    )

    exploracoes = [
        (
            ":material/trending_up:",
            "Oferta integral plena e IDEB",
            "Evolução da oferta integral plena e comparação do IDEB entre os tipos de oferta.",
            paginas["integral_parcial"],
        ),
        (
            ":material/map:",
            "Indicadores educacionais e IDEB",
            "Mapa com escolas, indicadores educacionais e suas associações com o IDEB.",
            paginas["visao_geral"],
        ),
        (
            ":material/analytics:",
            "Características das escolas e IDEB",
            "Associações entre características escolares e resultados do IDEB.",
            paginas["caracteristicas_ideb"],
        ),
        (
            ":material/school:",
            "Histórico por escola",
            "Indicadores por escola e comparação com a GRE e a rede estadual.",
            paginas["escola"],
        ),
    ]

    for inicio in range(0, len(exploracoes), 2):
        colunas = st.columns(2, gap="medium")
        for coluna, (icone, titulo, descricao, pagina) in zip(
            colunas, exploracoes[inicio : inicio + 2]
        ):
            with coluna:
                with st.container(border=True):
                    st.page_link(
                        pagina,
                        label=f"{titulo}\n\n{descricao}",
                        icon=icone,
                        use_container_width=True,
                    )

    st.divider()
    st.caption(
        "**Sobre os dados:** O painel reúne informações do INEP (Censo Escolar, IDEB, "
        "taxas de rendimento e indicadores educacionais) sobre as escolas estaduais da "
        "Paraíba que ofertam Ensino Médio, de 2016 a 2025. Neste estudo, são "
        "classificadas como **Integral Plena** as escolas com 100% das matrículas do "
        "Ensino Médio em tempo integral; as demais são classificadas como **Parcial ou "
        "Mista**."
    )
