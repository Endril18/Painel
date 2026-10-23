REF_IDEB = 4.4
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
    "Nota de infraestrutura (0-100)": ("IDX_INFRAESTRUTURA", "", True, False),
    "Nota de tecnologia (0-100)": ("IDX_TECNOLOGIA", "", True, False),
}

FICHA = [
    ("Matrículas no Ensino Médio", "QT_MAT_MED", "", 0),
    ("Turmas", "QT_TUR_MED", "", 0),
    ("Docentes", "QT_DOC_MED", "", 0),
    ("Alunos por turma", "ALUNOS_POR_TURMA", "", 1),
    ("Alunos por docente", "ALUNOS_POR_DOCENTE", "", 1),
    ("Matrículas em tempo integral", "PCT_INT", "%", 0),
    ("Computadores por 100 alunos", "COMPUTADORES_ALUNO_P100", "", 1),
    ("Nota de infraestrutura (0-100)", "IDX_INFRAESTRUTURA", "", 0),
    ("Nota de tecnologia (0-100)", "IDX_TECNOLOGIA", "", 0),
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
    "Nota de infraestrutura (0-100)",
    "Nota de tecnologia (0-100)",
]

LOCALIZACAO = {1: "Urbana", 2: "Rural"}
