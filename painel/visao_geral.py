import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from painel.config import ANOS_IDEB, PB_CENTRO, REF_IDEB
from painel.dados import formatar
from painel.mapas import (
    ScatterMap,
    adicionar_municipios_paraiba,
    aplicar_layout_mapa,
)


def renderizar(
    df, ano, indicador_label, indicador, tipo, gres_sel, mun_sel, busca,
):
    coluna, unidade, melhor_maior, so_anos_ideb = indicador
    d = df[df["NU_ANO_CENSO"] == ano].copy()
    if tipo != "Todas":
        d = d[d["TIPO_OFERTA"] == tipo]
    if gres_sel:
        d = d[d["GRE"].isin(gres_sel)]
    if mun_sel:
        d = d[d["NO_MUNICIPIO"].isin(mun_sel)]
    if busca:
        d = d[d["NO_ENTIDADE"].str.contains(busca, case=False, na=False)]

    if so_anos_ideb and ano not in ANOS_IDEB:
        st.info(
            f"O **{indicador_label}** só existe nos anos de aplicação do IDEB "
            f"({', '.join(map(str, ANOS_IDEB))}). Em {ano} não há dado; "
            "escolha um desses anos ou outro indicador."
        )
    if so_anos_ideb and ano == 2021:
        st.warning(
            "Em 2021 a cobertura do IDEB é baixa (efeitos da pandemia). "
            "Evite interpretar este ano isoladamente."
        )

    d_ind = d.dropna(subset=[coluna])
    n_total = len(d)
    n_com_dado = len(d_ind)

    if n_total == 0:
        st.warning("Nenhuma escola encontrada com os filtros selecionados.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Escolas no filtro", f"{n_total}")
    c2.metric(f"Com dado de {indicador_label.split(' (')[0]}", f"{n_com_dado}")
    c3.metric(
        "Mediana do indicador",
        formatar(d_ind[coluna].median(), unidade) if n_com_dado else "sem dado",
    )
    if coluna == "IDEB" and n_com_dado:
        pct = (d_ind["IDEB"] >= REF_IDEB).mean() * 100
        c4.metric(f"Com IDEB ≥ {str(REF_IDEB).replace('.', ',')}", f"{pct:.0f}%")
    else:
        c4.metric("Escolas integrais", f"{(d['TIPO_OFERTA'] == 'Integral').mean() * 100:.0f}%")

    st.subheader("Mapa das escolas")
    d_map = d.dropna(subset=["LATITUDE", "LONGITUDE"])
    sem_coord = d[d["LATITUDE"].isna() | d["LONGITUDE"].isna()]

    def texto_hover(r):
        linhas = [
            f"<b>{r.NO_ENTIDADE}</b>",
            f"{r.NO_MUNICIPIO} · {r.GRE}",
            f"{indicador_label}: {formatar(r.VALOR, unidade)}",
            f"Oferta: {r.TIPO_OFERTA}",
        ]
        if r.COORD_APROX == 1:
            linhas.append("<i>Localização aproximada</i>")
        return "<br>".join(linhas)

    d_map = d_map.assign(VALOR=d_map[coluna])
    d_map["HOVER"] = [texto_hover(r) for r in d_map.itertuples()]

    fig = go.Figure()
    adicionar_municipios_paraiba(fig)
    sem_valor = d_map[d_map["VALOR"].isna()]
    com_valor = d_map[d_map["VALOR"].notna()]

    if len(sem_valor):
        fig.add_trace(
            ScatterMap(
                lat=sem_valor["LATITUDE"],
                lon=sem_valor["LONGITUDE"],
                mode="markers",
                marker=dict(size=8, color="#9e9e9e", opacity=0.7),
                text=sem_valor["HOVER"],
                hoverinfo="text",
            )
        )
    if len(com_valor):
        escala = {True: "RdYlGn", False: "RdYlGn_r", None: "Viridis"}[melhor_maior]
        fig.add_trace(
            ScatterMap(
                lat=com_valor["LATITUDE"],
                lon=com_valor["LONGITUDE"],
                mode="markers",
                marker=dict(
                    size=10,
                    color=com_valor["VALOR"],
                    colorscale=escala,
                    showscale=True,
                    colorbar=dict(title=indicador_label.split(" (")[0], len=0.7),
                    opacity=0.9,
                ),
                text=com_valor["HOVER"],
                hoverinfo="text",
            )
        )
    aplicar_layout_mapa(
        fig, PB_CENTRO, 6.6, 560, estilo="white-bg"
    )
    st.plotly_chart(fig, use_container_width=True)

    notas = []
    if (d_map["COORD_APROX"] == 1).any():
        notas.append(
            f"{int((d_map['COORD_APROX'] == 1).sum())} escola(s) com localização aproximada "
            "(dividem o mesmo ponto com outra escola do município)."
        )
    if len(sem_coord):
        notas.append(f"{len(sem_coord)} escola(s) sem localização no mapa.")
    if n_com_dado < n_total:
        notas.append(
            f"{n_total - n_com_dado} escola(s) sem dado para este indicador em {ano} (pontos cinza)."
        )
    if notas:
        st.caption(" ".join(notas))

    if len(sem_coord):
        with st.expander("Escolas sem localização no mapa"):
            st.dataframe(
                sem_coord[["NO_ENTIDADE", "NO_MUNICIPIO", "GRE"]].rename(
                    columns={"NO_ENTIDADE": "Escola", "NO_MUNICIPIO": "Município"}
                ),
                hide_index=True,
                use_container_width=True,
            )

    if n_com_dado == 0:
        return

    col_dist, col_rank = st.columns(2)
    with col_dist:
        st.subheader("Distribuição de Ofertas")
        hist = px.histogram(
            d_ind,
            x=coluna,
            nbins=20,
            color="TIPO_OFERTA",
            color_discrete_map={"Integral": "#1f77b4", "Parcial": "#ff7f0e"},
            labels={coluna: indicador_label, "TIPO_OFERTA": "Oferta"},
            barmode="overlay",
            opacity=0.65,
        )
        hist.update_layout(
            template="plotly_white",
            height=450,
            margin=dict(l=0, r=0, t=40, b=0),
            yaxis_title="Escolas")
        if coluna == "IDEB":
            hist.add_vline(
                x=REF_IDEB,
                line_dash="dash",
                line_color="#555",
                annotation_text=f"Referência {str(REF_IDEB).replace('.', ',')}",
                annotation_position="top",
            )
        st.plotly_chart(hist, use_container_width=True)

    with col_rank:
        st.subheader("Panorama Estadual — Ranking Municipal")
        tabela_base = d_ind[["NO_ENTIDADE", "NO_MUNICIPIO", "GRE", "TIPO_OFERTA", coluna]].rename(
            columns={
                "NO_ENTIDADE": "Escola",
                "NO_MUNICIPIO": "Município",
                "TIPO_OFERTA": "Oferta",
                coluna: indicador_label,
            }
        )
        cfg = {indicador_label: st.column_config.NumberColumn(format="%.2f")}
        st.dataframe(
            tabela_base.sort_values(
                indicador_label,
                ascending=melhor_maior is False,
                kind="stable",
            ),
            hide_index=True,
            use_container_width=True,
            height="auto",
            column_config=cfg,
        )
        if melhor_maior is False:
            st.caption("Neste indicador, valores menores indicam melhor situação.")
        elif melhor_maior is None:
            st.caption(
                "Este indicador descreve o perfil da escola; "
                "maior ou menor não significa melhor ou pior."
            )
