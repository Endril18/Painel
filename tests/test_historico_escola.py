import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from streamlit.testing.v1 import AppTest

from painel import escola
from painel.config import ANOS_IDEB, INDICADORES, METAS_IDEB
from painel.dados import carregar_dados


class HistoricoEscolaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, _ = carregar_dados()
        cls.anos = sorted(cls.df.NU_ANO_CENSO.unique())
        cls.codigo = 25036300

    def renderizar(self, dados, indicador):
        with patch.object(escola, "st") as st:
            st.selectbox.side_effect = [self.codigo, indicador]
            escola.renderizar(dados, self.anos)
            st.radio.assert_not_called()
            st.metric.assert_not_called()
            st.dataframe.assert_not_called()
            self.assertEqual(st.selectbox.call_count, 2)
            return st.plotly_chart.call_args.args[0], st

    def test_series_e_medianas_preservadas_em_todos_indicadores(self):
        hist = self.df.loc[self.df.CO_ENTIDADE.eq(self.codigo)].sort_values("NU_ANO_CENSO")
        gre = hist.iloc[-1].GRE
        for indicador, (coluna, _, _, _) in INDICADORES.items():
            anos = [a for a in (ANOS_IDEB if coluna == "IDEB" else self.anos) if a in self.anos]
            esperadas = [
                hist.set_index("NU_ANO_CENSO")[coluna].reindex(anos),
                self.df.loc[self.df.GRE.eq(gre)].groupby("NU_ANO_CENSO")[coluna].median().reindex(anos),
                self.df.groupby("NU_ANO_CENSO")[coluna].median().reindex(anos),
            ]
            with self.subTest(indicador=indicador):
                figura, _ = self.renderizar(self.df, indicador)
                self.assertEqual(len(figura.data), 3)
                self.assertEqual(figura.layout.barmode, "group")
                for trace, esperado in zip(figura.data, esperadas):
                    self.assertEqual(trace.type, "bar")
                    esperado = esperado.dropna()
                    self.assertEqual(list(trace.x), esperado.index.tolist())
                    np.testing.assert_allclose(trace.y, esperado.values, equal_nan=True)
                if coluna == "IDEB":
                    self.assertEqual(figura.layout.shapes[0].y0, METAS_IDEB[max(self.anos)])

    def test_ausencias_nao_viram_zero_e_sao_explicitas(self):
        dados = self.df.copy()
        dados.loc[dados.CO_ENTIDADE.eq(self.codigo) & dados.NU_ANO_CENSO.eq(2019), "IDEB"] = np.nan
        figura, st = self.renderizar(dados, "IDEB")
        self.assertNotIn(2019, figura.data[0].x)
        for trace in figura.data[1:]:
            self.assertIn(2019, trace.x)
        mensagens = [call.args[0] for call in st.caption.call_args_list]
        self.assertTrue(any("Escola sem informação" in m and "2019" in m for m in mensagens))
        dados.loc[dados.CO_ENTIDADE.eq(self.codigo), "IDEB"] = np.nan
        _, st = self.renderizar(dados, "IDEB")
        st.caption.assert_any_call("A escola não tem dado deste indicador em nenhum ano.")

    def test_navegacao_e_identificacao(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Histórico por escola" in s.value for s in app.subheader))
        self.assertTrue(any(
            "Consulte a evolução dos indicadores de uma escola e compare seus resultados "
            "com as medianas da GRE e da rede estadual." in m.value
            for m in app.markdown
        ))
        link = next(item for item in app.get("page_link") if item.proto.page == "escola")
        self.assertEqual(link.proto.label, "Consultar histórico →")
        # AppTest.switch_page aceita apenas arquivos; a página é uma função.
        # Usa o destino registrado no próprio cartão para simular a navegação.
        app._page_hash = link.proto.page_script_hash
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.header[0].value, "Histórico por escola")
        self.assertEqual(len(app.selectbox), 1)
        app.selectbox[0].select(self.codigo).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual(len(app.selectbox), 2)
        self.assertEqual(len(app.metric), 0)
        self.assertEqual(len(app.dataframe), 0)
        self.assertEqual(len(app.get("plotly_chart")), 1)
        self.assertEqual(app.subheader[-1].value, "Histórico (2016–2025)")
        esc = self.df.loc[self.df.CO_ENTIDADE.eq(self.codigo)].sort_values("NU_ANO_CENSO").iloc[-1]
        identificacao = next(m.value for m in app.markdown if esc.NO_MUNICIPIO in m.value)
        for texto in [esc.GRE, "Zona", esc.TIPO_OFERTA]:
            self.assertIn(texto, identificacao)
        self.assertEqual(len(app.radio), 0)
        app.selectbox(key="ind_hist").select("Taxa de aprovação (%)").run()
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
