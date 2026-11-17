import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from painel.config import (
    ANOS_IDEB,
    COR_ESCOLA,
    COR_GRE,
    COR_REDE,
    INDICADORES,
    LOCALIZACAO,
    METAS_IDEB,
)


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
        st.info(
            "Selecione uma escola para consultar seu histórico e compará-lo "
            "com as medianas da GRE e da rede estadual."
        )
        return

    hist = df[df["CO_ENTIDADE"] == cod].sort_values("NU_ANO_CENSO")
    esc = hist.iloc[-1]
    gre = esc["GRE"]
    registros_oferta = hist.loc[hist["TIPO_OFERTA"].notna()]
    registro_oferta = registros_oferta.iloc[-1] if not registros_oferta.empty else esc
    tipo_oferta = registro_oferta["TIPO_OFERTA"]
    ano_oferta = int(registro_oferta["NU_ANO_CENSO"])

    st.subheader(esc["NO_ENTIDADE"])
    loc = LOCALIZACAO.get(int(esc["TP_LOCALIZACAO"]), "") if pd.notna(esc["TP_LOCALIZACAO"]) else ""
    st.markdown(
        f"**{esc['NO_MUNICIPIO']}** · {gre}" + (f" · Zona {loc.lower()}" if loc else "")
        + f" · {tipo_oferta} ({ano_oferta})"
    )
    anos_escola = sorted(hist["NU_ANO_CENSO"].unique())
    if anos_escola[-1] < ano_max:
        st.warning(
            f"Esta escola não aparece no Censo mais recente. "
            f"Dados disponíveis de {anos_escola[0]} a {anos_escola[-1]}."
        )

    st.divider()
    st.subheader("Histórico (2016–2025)")
    ind_label = st.selectbox("Indicador", list(INDICADORES.keys()), key="ind_hist")
    ind_col, ind_unidade, _, ind_ideb = INDICADORES[ind_label]

    anos_historico = [
        ano for ano in (ANOS_IDEB if ind_col == "IDEB" else anos) if ano in anos
    ]
    serie_escola = hist.set_index("NU_ANO_CENSO")[ind_col].reindex(anos_historico)
    serie_rede = (
        df.groupby("NU_ANO_CENSO")[ind_col].median().reindex(anos_historico)
    )
    serie_gre = (
        df[df["GRE"] == gre]
        .groupby("NU_ANO_CENSO")[ind_col]
        .median()
        .reindex(anos_historico)
    )

    series_historico = [
        (esc["NO_ENTIDADE"], serie_escola, COR_ESCOLA),
        (f"Mediana da {gre}", serie_gre, COR_GRE),
        ("Mediana da rede estadual", serie_rede, COR_REDE),
    ]

    fh = go.Figure()
    for nome, serie, cor in series_historico:
        serie_com_dado = serie.dropna()
        fh.add_trace(
            go.Bar(
                x=serie_com_dado.index,
                y=serie_com_dado.values,
                name=nome,
                marker_color=cor,
                offsetgroup=nome,
                hovertemplate=(
                    f"%{{x}}<br>{nome}: %{{y:.1f}}{ind_unidade}<extra></extra>"
                ),
            )
        )
    if ind_col == "IDEB":
        ref_ideb = METAS_IDEB.get(max(anos), 4.4)
        fh.add_hline(
            y=ref_ideb,
            line_dash="dot",
            line_color="#999",
            annotation_text=f"Referência {str(ref_ideb).replace('.', ',')}",
        )
    eixo_y = dict(title=ind_label, ticksuffix=ind_unidade, rangemode="tozero")
    fh.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(dtick=1, title=None),
        yaxis=eixo_y,
        legend=dict(orientation="h", y=-0.2),
        barmode="group",
    )

    st.plotly_chart(fh, use_container_width=True)
    anos_sem_dado = serie_escola.index[serie_escola.isna()].tolist()
    if anos_sem_dado:
        st.caption(
            "Escola sem informação para este indicador em: "
            + ", ".join(map(str, anos_sem_dado))
            + ". As medianas da GRE e da rede são exibidas quando disponíveis; "
            "a ausência de informação da escola não representa valor zero."
        )
    if serie_escola.notna().sum() == 0:
        st.caption("A escola não tem dado deste indicador em nenhum ano.")
    elif ind_ideb:
        st.caption(
            "Este indicador só existe nos anos de aplicação do IDEB "
            "(2017, 2019, 2021, 2023, 2025)."
        )
    else:
        st.caption("As barras aparecem somente nos anos com dado para cada série.")
    if ind_col == "IDEB":
        st.caption(
            "Os resultados do IDEB de 2021 devem ser interpretados com cautela "
            "devido à baixa cobertura daquela edição."
        )
