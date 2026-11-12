from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def carregar_dados():
    escolas = pd.read_parquet(DATA_DIR / "escolas.parquet")
    escola_ano = pd.read_parquet(DATA_DIR / "escola_ano.parquet")
    df = escola_ano.merge(escolas, on="CO_ENTIDADE", how="left", validate="m:1")
    # Esses indicadores eram exportados no Parquet anterior. Reconstituí-los
    # aqui mantém a ficha da escola compatível com a base atual, que contém os
    # quantitativos necessários para o cálculo.
    for coluna, denominador in {
        "ALUNOS_POR_TURMA": "QT_TUR_MED",
        "ALUNOS_POR_DOCENTE": "QT_DOC_MED",
    }.items():
        df[coluna] = df["QT_MAT_MED"].div(
            df[denominador].where(df[denominador].ne(0))
        )
    df["GRE"] = df["CO_ORGAO_REGIONAL"].apply(
        lambda x: f"{int(x)}ª GRE" if pd.notna(x) else "Sem GRE"
    )
    return df, escolas


@st.cache_data
def carregar_caracteristicas_ideb():
    """Carrega os resultados exportados para a seção Características e IDEB."""
    return pd.read_parquet(DATA_DIR / "correlacoes_censo_ideb.parquet")


@st.cache_data
def carregar_ensino_integral_ideb():
    """Carrega os resultados exibidos na seção Ensino integral e IDEB."""
    oferta = pd.read_parquet(DATA_DIR / "oferta_anual.parquet")
    ideb_oferta = pd.read_parquet(DATA_DIR / "ideb_por_oferta.parquet")
    testes_ideb = pd.read_parquet(DATA_DIR / "testes_ideb_oferta.parquet")
    return oferta, ideb_oferta, testes_ideb


def formatar(valor, unidade="", casas=1):
    if pd.isna(valor):
        return "sem dado"
    return f"{valor:.{casas}f}{unidade}".replace(".", ",")
