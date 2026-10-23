import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from painel.config import (
    COMPARACAO,
    COR_ESCOLA,
    COR_GRE,
    COR_REDE,
    FICHA,
    INDICADORES,
    LOCALIZACAO,
    REF_IDEB,
)
from painel.dados import formatar
from painel.mapas import ScatterMap, aplicar_layout_mapa


def renderizar(df, anos):
    ultimo = df.sort_values("NU_ANO_CENSO").groupby("CO_ENTIDADE").tail(1)
    ano_max = max(anos)
    rotulos = {}
    for r in ultimo.itertuples():
        rot = f"{r.NO_ENTIDADE} — {r.NO_MUNICIPIO}"
        if r.NU_ANO_CENSO < ano_max:
            rot += f" (dados até {r.NU_ANO_CENSO})"
        rotulos[r.CO_ENTIDADE] = rot
    codigos = sorted(rotulos, key=lambda c: rotulos[c])

    cod = st.selectbox(
        "Escolha a escola (digite para buscar)",
        codigos,
        format_func=lambda c: rotulos[c],
        index=None,
        placeholder="Nome da escola ou município",
    )
    if cod is None:
        st.info("Selecione uma escola para ver a ficha, o histórico e a comparação com a rede.")
        return

    hist = df[df["CO_ENTIDADE"] == cod].sort_values("NU_ANO_CENSO")
    esc = hist.iloc[-1]
    gre = esc["GRE"]

    st.header(esc["NO_ENTIDADE"])
    loc = LOCALIZACAO.get(int(esc["TP_LOCALIZACAO"]), "") if pd.notna(esc["TP_LOCALIZACAO"]) else ""
    st.markdown(
        f"**{esc['NO_MUNICIPIO']}** · {gre}" + (f" · Zona {loc.lower()}" if loc else "")
        + f" · {esc['TIPO_OFERTA']}"
    )
    anos_escola = sorted(hist["NU_ANO_CENSO"].unique())
    if anos_escola[-1] < ano_max:
        st.warning(
            f"Esta escola não aparece no Censo mais recente. "
            f"Dados disponíveis de {anos_escola[0]} a {anos_escola[-1]}."
        )

    col_ficha, col_mapa = st.columns([3, 2])
    with col_ficha:
        ano_f = st.selectbox(
            "Ano da ficha",
            anos_escola,
            index=len(anos_escola) - 1,
            key="ano_ficha",
        )
        linha = hist[hist["NU_ANO_CENSO"] == ano_f].iloc[0]
        ref_ano = df[df["NU_ANO_CENSO"] == ano_f]
        st.caption(
            f"Em cada item, a mediana da rede estadual em {ano_f} aparece abaixo do valor."
        )
        cols = st.columns(5)
        for i, (rot, col, un, casas) in enumerate(FICHA):
            with cols[i % 5]:
                st.metric(rot, formatar(linha[col], un, casas))
                st.caption(f"Rede: {formatar(ref_ano[col].median(), un, casas)}")
        extra = []
        extra.append(
            "Oferece EJA no Ensino Médio"
            if linha["TEM_EJA"] == 1
            else "Sem EJA no Ensino Médio"
        )
        st.caption(" · ".join(extra))

    with col_mapa:
        if pd.notna(esc["LATITUDE"]) and pd.notna(esc["LONGITUDE"]):
            fm = go.Figure(
                ScatterMap(
                    lat=[esc["LATITUDE"]],
                    lon=[esc["LONGITUDE"]],
                    mode="markers",
                    marker=dict(size=14, color=COR_ESCOLA),
                    text=[esc["NO_ENTIDADE"]],
                    hoverinfo="text",
                )
            )
            aplicar_layout_mapa(
                fm,
                {"lat": esc["LATITUDE"], "lon": esc["LONGITUDE"]},
                12,
                300,
            )
            st.plotly_chart(fm, use_container_width=True)
            if esc["COORD_APROX"] == 1:
                st.caption("Localização aproximada (referência do município).")
        else:
            st.info("Esta escola não tem localização no mapa.")

    st.subheader("Histórico (2016–2025)")
    ind_label = st.selectbox("Indicador", list(INDICADORES.keys()), key="ind_hist")
    ind_col, _, _, ind_ideb = INDICADORES[ind_label]

    serie_escola = hist.set_index("NU_ANO_CENSO")[ind_col].reindex(anos)
    serie_rede = df.groupby("NU_ANO_CENSO")[ind_col].median().reindex(anos)
    serie_gre = (
        df[df["GRE"] == gre]
        .groupby("NU_ANO_CENSO")[ind_col]
        .median()
        .reindex(anos)
    )

    fh = go.Figure()
    for nome, serie, cor, dash in [
        (esc["NO_ENTIDADE"], serie_escola, COR_ESCOLA, "solid"),
        (f"Mediana da {gre}", serie_gre, COR_GRE, "dash"),
        ("Mediana da rede estadual", serie_rede, COR_REDE, "dot"),
    ]:
        fh.add_trace(
            go.Scatter(
                x=anos,
                y=serie.values,
                mode="lines+markers",
                name=nome,
                line=dict(color=cor, dash=dash, width=3 if cor == COR_ESCOLA else 2),
                connectgaps=True,
            )
        )
    if ind_col == "IDEB":
        fh.add_hline(
            y=REF_IDEB,
            line_dash="dot",
            line_color="#999",
            annotation_text=f"Referência {str(REF_IDEB).replace('.', ',')}",
        )
    fh.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(dtick=1, title=None),
        yaxis_title=ind_label,
        legend=dict(orientation="h", y=-0.2),
    )

    st.plotly_chart(fh, use_container_width=True)
    if serie_escola.notna().sum() == 0:
        st.caption("A escola não tem dado deste indicador em nenhum ano.")
    elif ind_ideb:
        st.caption(
            "Este indicador só existe nos anos de aplicação do IDEB "
            "(2017, 2019, 2021, 2023, 2025); as linhas ligam os anos com dado. "
        )

    st.subheader(f"Comparação em {ano_f}")
    ref_gre = ref_ano[ref_ano["GRE"] == gre]
    linhas = []
    for rot in COMPARACAO:
        col, _, _, _ = INDICADORES[rot]
        linhas.append(
            {
                "Indicador": rot,
                "Escola": linha[col],
                f"Mediana da {gre}": ref_gre[col].median(),
                "Mediana da rede": ref_ano[col].median(),
            }
        )
    comp = pd.DataFrame(linhas)
    st.dataframe(
        comp.style.format(
            {
                c: (
                    lambda v: "sem dado"
                    if pd.isna(v)
                    else f"{v:.1f}".replace(".", ",")
                )
                for c in comp.columns[1:]
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.caption(
        f"Medianas calculadas entre as escolas estaduais com dado no ano "
        f"({len(ref_gre)} escolas na {gre}, {len(ref_ano)} na rede). "
        "Para taxas de reprovação, abandono, distorção idade-série e esforço "
        "docente, valores menores indicam melhor situação."
    )

    st.subheader("Taxas de rendimento da escola")
    tx = hist[
        ["NU_ANO_CENSO", "TX_APROV_MED", "TX_REPROV_MED", "TX_ABAND_MED"]
    ].melt(id_vars="NU_ANO_CENSO", var_name="Taxa", value_name="Percentual")
    tx["Taxa"] = tx["Taxa"].map(
        {
            "TX_APROV_MED": "Aprovação",
            "TX_REPROV_MED": "Reprovação",
            "TX_ABAND_MED": "Abandono",
        }
    )
    ft = px.line(
        tx,
        x="NU_ANO_CENSO",
        y="Percentual",
        color="Taxa",
        markers=True,
        color_discrete_map={
            "Aprovação": "#2ca02c",
            "Reprovação": "#d62728",
            "Abandono": "#9467bd",
        },
        labels={"NU_ANO_CENSO": ""},
    )
    ft.update_layout(
        template="plotly_white",
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", y=-0.2),
    )

    st.plotly_chart(ft, use_container_width=True)