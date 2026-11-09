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
    """Carrega os resultados exportados para a seção Características e IDEB."""
    return pd.read_parquet(DATA_DIR / "correlacoes_ideb.parquet")


@st.cache_data
def carregar_integral_parcial():
    """Carrega os resultados analíticos exportados para a página Integral × Parcial."""
    oferta = pd.read_parquet(DATA_DIR / "oferta_anual.parquet")
    ideb_oferta = pd.read_parquet(DATA_DIR / "ideb_por_oferta.parquet")
    transicoes = pd.read_parquet(DATA_DIR / "transicoes_ideb.parquet")
    evolucao_grupos = pd.read_parquet(DATA_DIR / "evolucao_grupos.parquet")
    return oferta, ideb_oferta, transicoes, evolucao_grupos


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
