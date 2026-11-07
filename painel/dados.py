from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def carregar_dados():
    escolas = pd.read_parquet(DATA_DIR / "escolas.parquet")
    escola_ano = pd.read_parquet(DATA_DIR / "escola_ano.parquet")
    df = escola_ano.merge(escolas, on="CO_ENTIDADE", how="left", validate="m:1")
    df["GRE"] = df["CO_ORGAO_REGIONAL"].apply(
        lambda x: f"{int(x)}ª GRE" if pd.notna(x) else "Sem GRE"
    )
    return df, escolas


@st.cache_data
def carregar_caracteristicas_ideb():
    perfil = pd.read_parquet(DATA_DIR / "perfil_ideb_2025.parquet")
    correlacoes = pd.read_parquet(DATA_DIR / "correlacoes_ideb.parquet")
    return perfil, correlacoes


def formatar(valor, unidade="", casas=1):
    if pd.isna(valor):
        return "sem dado"
    return f"{valor:.{casas}f}{unidade}".replace(".", ",")
