import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from painel.barras_correlacoes import criar_lista_correlacoes
from painel.correlacoes_indicadores import (
    ANOS,
    INDICADORES,
    carregar_correlacoes,
    criar_mapa_correlacoes,
)


PAGINA = """
from painel.dados import carregar_dados
from painel.visao_geral import renderizar_com_filtros
df, _ = carregar_dados()
renderizar_com_filtros(df, sorted(df.NU_ANO_CENSO.unique()))
"""
NUMERICOS = "Ver resultados numéricos das correlações"
COMPARACAO = "Comparar correlações entre edições (2017–2025)"


def expansor(app, titulo):
    return next(item for item in app.expander if item.label == titulo)


class CorrelacoesIndicadoresTest(unittest.TestCase):
    def pagina(self):
        return AppTest.from_string(PAGINA, default_timeout=30).run()

    def sem_erros(self, app):
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)

    def test_ano_controla_barras_e_tabela_sem_substituir_edicoes(self):
        app = self.pagina()
        fonte = carregar_correlacoes()
        comparacao = expansor(app, COMPARACAO).get("plotly_chart")[0].proto.spec
        self.assertEqual(len(app.select_slider), 1)
        self.assertEqual(len(app.selectbox), 1)  # Indicador; nenhum seletor extra.
        for ano in range(2016, 2026):
            with self.subTest(ano=ano):
                app.select_slider[0].set_value(ano).run()
                self.sem_erros(app)
                self.assertEqual(
                    expansor(app, COMPARACAO).get("plotly_chart")[0].proto.spec,
                    comparacao,
                )
                numericos = expansor(app, NUMERICOS)
                if ano not in ANOS:
                    self.assertEqual(len(app.get("html")), 0)
                    self.assertEqual(len(numericos.dataframe), 0)
                    self.assertTrue(any(
                        f"ano selecionado ({ano})" in item.value for item in app.info
                    ))
                    continue
                esperado = fonte.loc[
                    fonte.ano.eq(ano) & fonte.indicador.isin(INDICADORES),
                    ["ano", "indicador", "n", "correlacao", "p_ajustado"],
                ].sort_values("correlacao", key=lambda s: s.abs(), ascending=False, kind="stable")
                pd.testing.assert_frame_equal(numericos.dataframe[0].value, esperado)
                barras = app.get("html")[0].proto.body
                posicoes = [barras.index(nome) for nome in esperado.indicador]
                self.assertEqual(posicoes, sorted(posicoes))
                for linha in esperado.itertuples():
                    sinal = "−" if linha.correlacao < 0 else "+" if linha.correlacao > 0 else ""
                    coef = f"{sinal}{abs(linha.correlacao):.3f}".replace(".", ",")
                    marca = "*" if linha.p_ajustado < 0.05 else ""
                    self.assertIn(f"<span>{coef}{marca}</span>", barras)

    def test_filtros_locais_nao_alteram_resultados_estaduais(self):
        app = self.pagina()
        tabela = expansor(app, NUMERICOS).dataframe[0].value.copy()
        barras = app.get("html")[0].proto.body
        app.radio[0].set_value("Integral Plena").run()
        app.multiselect[0].set_value(["1ª GRE"]).run()
        app.multiselect[1].set_value([app.multiselect[1].options[0]]).run()
        app.selectbox[0].select("Taxa de aprovação (%)").run()
        self.sem_erros(app)
        pd.testing.assert_frame_equal(expansor(app, NUMERICOS).dataframe[0].value, tabela)
        self.assertEqual(app.get("html")[0].proto.body, barras)
        app.text_input[0].set_value("ESCOLA_INEXISTENTE_TESTE").run()
        self.sem_erros(app)
        self.assertTrue(any("Nenhuma escola" in item.value for item in app.warning))
        pd.testing.assert_frame_equal(expansor(app, NUMERICOS).dataframe[0].value, tabela)
        self.assertEqual(app.get("html")[0].proto.body, barras)

    def test_heatmap_preserva_resultados_das_quatro_edicoes(self):
        fonte = carregar_correlacoes()
        mapa = criar_mapa_correlacoes(fonte).data[0]
        self.assertEqual(list(mapa.x), [str(ano) for ano in ANOS])
        for i, indicador in enumerate(INDICADORES):
            for j, ano in enumerate(ANOS):
                linha = fonte.loc[fonte.ano.eq(ano) & fonte.indicador.eq(indicador)].iloc[0]
                self.assertEqual(mapa.z[i][j], linha.correlacao)
                self.assertEqual(mapa.customdata[i][j][0], linha.n)
                self.assertEqual(mapa.customdata[i][j][1], linha.p_ajustado)

    def test_componente_usa_escala_fixa_e_limiar_estrito(self):
        html = criar_lista_correlacoes(pd.DataFrame({
            "nome": ["Negativo <teste>", "Positivo", "Zero"],
            "correlacao": [-1.0, 0.5, 0.0],
            "p_ajustado": [0.049, 0.05, 0.2],
        }), mostrar_significancia=True)
        self.assertIn("Negativo &lt;teste&gt;", html)
        self.assertIn("<span>−1,000*</span>", html)
        self.assertIn("<span>+0,500</span>", html)
        self.assertIn('width: 50.000%;', html)
        self.assertIn('width: 25.000%;', html)
        self.assertIn('width: 0.000%;', html)
        self.assertIn("<span>−1</span><span>0</span><span>+1</span>", html)

    def test_caracteristicas_continua_usando_componente(self):
        app = AppTest.from_string(
            "from painel.caracteristicas_ideb import renderizar\nrenderizar()",
            default_timeout=30,
        ).run()
        self.sem_erros(app)
        self.assertEqual(len(app.get("html")), 1)
        self.assertEqual(app.get("html")[0].proto.body.count('class="correlacao-item"'), 7)
        self.assertIn("Refeitório", app.get("html")[0].proto.body)
        self.assertIn(
            "Refeitório",
            expansor(app, NUMERICOS).dataframe[0].value["Característica"].tolist(),
        )
        self.assertEqual(len(app.get("plotly_chart")), 1)


if __name__ == "__main__":
    unittest.main()
