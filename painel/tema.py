import streamlit as st


def aplicar_estilos(modo_escuro):
    marcador = '<div class="painel-tema-escuro"></div>' if modo_escuro else ""
    st.markdown(
        marcador
        + """
        <style>
        [data-testid="stMainBlockContainer"] {
            padding-top: 1rem;
        }
        body:has(.painel-tema-escuro) [data-testid="stAppViewContainer"],
        body:has(.painel-tema-escuro) [data-testid="stSidebar"] {
            background-color: #0e1117;
            color: #fafafa;
        }
        body:has(.painel-tema-escuro) [data-testid="stHeader"] {
            background-color: #0e1117;
        }
        body:has(.painel-tema-escuro) [data-testid="stMarkdownContainer"],
        body:has(.painel-tema-escuro) [data-testid="stWidgetLabel"],
        body:has(.painel-tema-escuro) [data-testid="stCaptionContainer"] {
            color: #fafafa;
        }
        body:has(.painel-tema-escuro) [data-testid="stTextInput"] input,
        body:has(.painel-tema-escuro) [data-baseweb="select"] > div,
        body:has(.painel-tema-escuro) [data-baseweb="tag"] {
            background-color: #262730;
            color: #fafafa;
        }
        body:has(.painel-tema-escuro) [data-testid="stDataFrame"] {
            color-scheme: dark;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def aplicar_tema_grafico(fig, modo_escuro):
    template = "plotly_dark" if modo_escuro else "plotly_white"
    cor_fundo = "#0e1117" if modo_escuro else "#ffffff"
    fig.update_layout(
        template=template,
        paper_bgcolor=cor_fundo,
        plot_bgcolor=cor_fundo,
    )
