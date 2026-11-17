"""Componente compartilhado de barras divergentes para correlações exportadas."""

from html import escape
from textwrap import dedent

import pandas as pd


def formatar_coeficiente(valor: float) -> str:
    if pd.isna(valor):
        return "—"
    if valor > 0:
        sinal = "+"
    elif valor < 0:
        sinal = "−"
    else:
        sinal = ""
    return f"{sinal}{abs(valor):.3f}".replace(".", ",")


def formatar_p_ajustado(valor: float) -> str:
    if pd.isna(valor):
        return "—"
    return "< 0,001" if valor < 0.001 else f"{valor:.3f}".replace(".", ",")


def criar_lista_correlacoes(
    dados: pd.DataFrame, *, mostrar_significancia: bool = False
) -> str:
    """Cria a lista divergente com escala visual fixa de -1 a +1."""
    itens = []
    for linha in dados.itertuples(index=False):
        valor = float(linha.correlacao)
        classe = "negativa" if valor < 0 else "positiva"
        largura = min(abs(valor), 1) * 50
        nome = escape(linha.nome)
        coeficiente = formatar_coeficiente(valor)
        if mostrar_significancia and linha.p_ajustado < 0.05:
            coeficiente += "*"
        itens.append(
            f"""
            <div class="correlacao-item">
                <div class="correlacao-cabecalho">
                    <span>{nome}</span>
                    <span>{coeficiente}</span>
                </div>
                <div class="correlacao-trilha" aria-label="{nome}: {coeficiente}">
                    <span class="correlacao-barra correlacao-barra--{classe}"
                          style="width: {largura:.3f}%;"></span>
                </div>
            </div>
            """
        )

    return dedent(f"""
    <style>
        .correlacao-lista {{
            width: 100%;
        }}
        .correlacao-item {{
            margin: 0 0 1.1rem;
        }}
        .correlacao-cabecalho {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
            margin-bottom: 0.35rem;
            color: inherit;
            font-size: 0.95rem;
        }}
        .correlacao-cabecalho span:first-child {{
            min-width: 0;
            overflow-wrap: anywhere;
        }}
        .correlacao-cabecalho span:last-child {{
            flex: 0 0 auto;
            font-variant-numeric: tabular-nums;
            font-weight: 600;
        }}
        .correlacao-trilha {{
            position: relative;
            height: 0.8rem;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(127, 127, 127, 0.18);
        }}
        .correlacao-trilha::before {{
            position: absolute;
            z-index: 1;
            top: -0.15rem;
            bottom: -0.15rem;
            left: 50%;
            width: 1px;
            background: currentColor;
            content: "";
            opacity: 0.55;
        }}
        .correlacao-barra {{
            position: absolute;
            top: 0;
            bottom: 0;
            display: block;
        }}
        .correlacao-barra--negativa {{
            right: 50%;
            border-radius: 999px 0 0 999px;
            background: #d9534f;
        }}
        .correlacao-barra--positiva {{
            left: 50%;
            border-radius: 0 999px 999px 0;
            background: #2f6fbd;
        }}
        .correlacao-escala {{
            display: flex;
            justify-content: space-between;
            margin-top: 0.25rem;
            color: inherit;
            font-size: 0.75rem;
            opacity: 0.7;
        }}
        @media (max-width: 640px) {{
            .correlacao-item {{
                margin-bottom: 0.95rem;
            }}
            .correlacao-cabecalho {{
                font-size: 0.9rem;
            }}
        }}
    </style>
    <div class="correlacao-lista">
        {''.join(itens)}
        <div class="correlacao-escala">
            <span>−1</span><span>0</span><span>+1</span>
        </div>
    </div>
    """).lstrip()


