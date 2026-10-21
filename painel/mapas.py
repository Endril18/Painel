import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st


USA_MAP_NOVO = hasattr(go, "Scattermap")
ScatterMap = go.Scattermap if USA_MAP_NOVO else go.Scattermapbox
ChoroplethMap = (
    go.Choroplethmap if hasattr(go, "Choroplethmap") else go.Choroplethmapbox
)


@st.cache_data
def carregar_municipios_paraiba():
    caminho = Path(__file__).resolve().parent.parent / "data" / "municipios.geojson"
    with caminho.open(encoding="utf-8") as arquivo:
        geojson = json.load(arquivo)
    if geojson.get("type") != "FeatureCollection" or not geojson.get("features"):
        raise ValueError(f"GeoJSON inválido ou sem municípios: {caminho}")
    return geojson


def adicionar_municipios_paraiba(fig):
    geojson = carregar_municipios_paraiba()
    ids = [feature["properties"]["id"] for feature in geojson["features"]]
    fig.add_trace(
        ChoroplethMap(
            geojson=geojson,
            locations=ids,
            z=[0] * len(ids),
            featureidkey="properties.id",
            colorscale=[[0, "#f3f6f9"], [1, "#f3f6f9"]],
            zmin=0,
            zmax=1,
            marker_line_color="#9aa8b5",
            marker_line_width=0.5,
            showscale=False,
            hoverinfo="skip",
            showlegend=False,
        )
    )


def aplicar_layout_mapa(fig, centro, zoom, altura, estilo="open-street-map"):
    cfg = dict(style=estilo, center=centro, zoom=zoom)
    if USA_MAP_NOVO:
        fig.update_layout(map=cfg)
    else:
        fig.update_layout(mapbox=cfg)
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)



