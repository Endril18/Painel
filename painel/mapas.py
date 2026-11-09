import json
import math
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
            colorscale=[[0, "#feffff"], [1, "#feffff"]],
            zmin=0,
            zmax=1,
            marker_line_color="#9aa8b5",
            marker_line_width=0.5,
            showscale=False,
            hoverinfo="skip",
            showlegend=False,
        )
    )


def _iterar_coordenadas(geometria):
    """Retorna todos os pares longitude/latitude de uma geometria GeoJSON."""
    tipo = geometria.get("type")
    coordenadas = geometria.get("coordinates")

    if tipo == "GeometryCollection":
        for geometria_filha in geometria.get("geometries", []):
            yield from _iterar_coordenadas(geometria_filha)
        return

    def percorrer(valor):
        if (
            isinstance(valor, (list, tuple))
            and len(valor) >= 2
            and all(isinstance(item, (int, float)) for item in valor[:2])
        ):
            yield float(valor[0]), float(valor[1])
            return
        for item in valor or []:
            yield from percorrer(item)

    yield from percorrer(coordenadas)


def limites_municipios(codigos):
    """Calcula os limites combinados dos municípios pelos códigos IBGE."""
    codigos = {str(codigo) for codigo in codigos if codigo is not None}
    if not codigos:
        return None

    pontos = []
    for feature in carregar_municipios_paraiba()["features"]:
        codigo = str(feature.get("properties", {}).get("id"))
        if codigo in codigos:
            pontos.extend(_iterar_coordenadas(feature.get("geometry", {})))

    if not pontos:
        return None

    longitudes, latitudes = zip(*pontos)
    return {
        "west": min(longitudes),
        "east": max(longitudes),
        "south": min(latitudes),
        "north": max(latitudes),
    }


def calcular_enquadramento_municipios(
    codigos, margem=0.08, largura_referencia=480, altura=560,
    zoom_minimo=8.5, zoom_maximo=12.5,
):
    """Retorna centro e zoom para enquadrar municípios selecionados.

    O zoom máximo evita uma aproximação exagerada em municípios pequenos ou
    com uma única escola. A largura de referência é deliberadamente
    conservadora para preservar a visualização em dispositivos móveis.
    """
    limites = limites_municipios(codigos)
    if limites is None:
        return None

    longitude = (limites["west"] + limites["east"]) / 2
    latitude = (limites["south"] + limites["north"]) / 2
    largura = max(limites["east"] - limites["west"], 0.04)
    altura_graus = max(limites["north"] - limites["south"], 0.04)
    largura += largura * margem * 2
    altura_graus += altura_graus * margem * 2

    # A escala vertical usa a projeção Web Mercator, como o mapa do Plotly.
    def mercator_y(lat):
        seno = min(max(math.sin(math.radians(lat)), -0.9999), 0.9999)
        return 0.5 - math.log((1 + seno) / (1 - seno)) / (4 * math.pi)

    longitude_normalizada = largura / 360
    latitude_normalizada = abs(
        mercator_y(latitude - altura_graus / 2)
        - mercator_y(latitude + altura_graus / 2)
    )
    zoom_longitude = math.log2(largura_referencia / (512 * longitude_normalizada))
    zoom_latitude = math.log2(altura / (512 * latitude_normalizada))
    zoom = min(zoom_longitude, zoom_latitude)
    zoom = max(zoom_minimo, min(zoom_maximo, zoom))

    return {
        "centro": {"lat": latitude, "lon": longitude},
        "zoom": round(zoom, 2),
    }


def aplicar_layout_mapa(
    fig, centro, zoom, altura, estilo="open-street-map"
):
    cfg = dict(style=estilo, center=centro, zoom=zoom)
    if USA_MAP_NOVO:
        fig.update_layout(map=cfg)
    else:
        fig.update_layout(mapbox=cfg)
    fig.update_layout(
        template="plotly_white",
        height=altura,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font_color="#1f2937",
    )

