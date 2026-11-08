METAS_IDEB = {2017: 4.0, 2019: 4.2, 2021: 4.4, 2023: 4.4, 2025: 4.4}
ANOS_IDEB = [2017, 2019, 2021, 2023, 2025]
PB_CENTRO = {"lat": -7.15, "lon": -36.75}
COR_ESCOLA = "#1f77b4"
COR_GRE = "#ff7f0e"
COR_REDE = "#7f7f7f"

INDICADORES = {
    "IDEB": ("IDEB", "", True, True),
    "Nota média padronizada (Saeb)": ("NOTA_MEDIA", "", True, True),
    "Nota de Matemática (Saeb)": ("NOTA_MAT", "", True, True),
    "Nota de Português (Saeb)": ("NOTA_PORT", "", True, True),
    "Indicador de rendimento (fluxo)": ("REND", "", True, True),
    "Taxa de aprovação (%)": ("TX_APROV_MED", "%", True, False),
    "Taxa de reprovação (%)": ("TX_REPROV_MED", "%", False, False),
    "Taxa de abandono (%)": ("TX_ABAND_MED", "%", False, False),
    "Distorção idade-série (%)": ("TDI_MED_CAT_0", "%", False, False),
    "Docentes com formação adequada (%)": ("AFD_ADEQUADA", "%", True, False),
    "Docentes com esforço alto (%)": ("IED_ESFORCO_ALTO", "%", False, False),
    "Complexidade da gestão (nível)": ("ICG_NIVEL", "", None, False),
}

FICHA = [
    ("Matrículas no Ensino Médio", "QT_MAT_MED", "", 0),
    ("Turmas", "QT_TUR_MED", "", 0),
    ("Docentes", "QT_DOC_MED", "", 0),
    ("Alunos por turma", "ALUNOS_POR_TURMA", "", 1),
    ("Alunos por docente", "ALUNOS_POR_DOCENTE", "", 1),
    ("Matrículas em tempo integral", "PCT_INT", "%", 0),
]

COMPARACAO = [
    "IDEB",
    "Taxa de aprovação (%)",
    "Taxa de reprovação (%)",
    "Taxa de abandono (%)",
    "Distorção idade-série (%)",
    "Docentes com formação adequada (%)",
    "Docentes com esforço alto (%)",
    "Complexidade da gestão (nível)",
]

LOCALIZACAO = {1: "Urbana", 2: "Rural"}
