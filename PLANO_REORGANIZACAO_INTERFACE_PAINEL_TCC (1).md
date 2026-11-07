# Plano de reorganização da interface — Painel do TCC

**Objetivo:** tornar o painel Streamlit coerente, fácil de navegar e simples de apresentar à banca, corrigindo os filtros globais que só funcionam na Visão geral e o uso de abas que acumulam conteúdo no mesmo fluxo.

**Escopo:** refatoração da interface existente. **Não** refazer análises, recalcular indicadores ou reexportar Parquets. Implementar em mudanças pequenas, testáveis, sem atrasar a criação das páginas restantes.

## 1. Diagnóstico do projeto atual

Os arquivos existentes são:

- `app.py`: `st.set_page_config`, `carregar_dados()`, filtros com `st.sidebar` criados globalmente e `st.tabs(["Visão geral", "Características e IDEB", "Escola"])`.
- `painel/visao_geral.py`: `renderizar(df, ano, indicador_label, indicador, tipo, gres_sel, mun_sel, busca)`; mapa, KPIs, distribuição e tabela.
- `painel/caracteristicas_ideb.py`: `renderizar(df)`; grupos alto × baixo, dispersão TDI × IDEB e correlações. Usa resultados pré-calculados.
- `painel/escola.py`: `renderizar(df, anos)`; seletor da escola, ficha, mapa, históricos e comparações.
- `painel/dados.py`: leitura de `data/escolas.parquet`, `data/escola_ano.parquet`, `data/perfil_ideb_2025.parquet`, `data/correlacoes_ideb.parquet`.
- `painel/config.py` e `painel/mapas.py`: dicionários e funções auxiliares.

### Problemas identificados

1. Os filtros da barra lateral são criados mesmo nas páginas que não os usam, confundindo o visitante.
2. `st.tabs` serve como abas de conteúdo, não como navegação real entre páginas; por padrão, o código das abas executa em cada rerun.
3. A hierarquia é pouco clara: título geral, nome da aba, título da seção, controles e gráficos longos se sucedem na mesma coluna.
4. Na página Características e IDEB há gráficos corretos, mas a leitura fica extensa e as interpretações essenciais ficam pouco destacadas.

## 2. Estrutura desejada

Navegação horizontal superior (nativa do Streamlit):

1. **Visão geral** — panorama estadual, filtros próprios, mapa, distribuição e tabela.
2. **Características e IDEB** — grupos alto/baixo, dispersão e mapa de calor.
3. **Escola** — busca, ficha, histórico e comparação.

**Preparada para incluir depois:** **Integral × Parcial** e **Sobre os dados e métodos**. **Não criar páginas vazias só para preencher o menu** nesta refatoração.

### Localização dos controles

| Página | Controles principais | Controles secundários |
|---|---|---|
| Visão geral | Ano, indicador e tipo de oferta no topo da página | GRE, município e busca por nome dentro de `st.expander("Filtros adicionais")` ou `st.popover`, se compatível com a versão instalada |
| Características e IDEB | Recorte da comparação (Todas / Só integrais / Só parciais) | Tipo de indicador e escolha da característica, junto do gráfico correspondente |
| Escola | Seletor de escola no início da página | Ano da ficha e indicador do histórico, próximos às seções onde são usados |
| Integral × Parcial (futura) | Apenas controles efetivamente aplicados aos dados dessa página | Nenhum filtro global implícito |
| Sobre (futura) | Sem filtros | — |

**Nunca** sugerir que os filtros da Visão geral afetam tabelas pré-calculadas das demais páginas.

## 3. Execução incremental para o Codex

### Etapa A — Proteger e observar a versão atual (obrigatória)

- [ ] Analisar `app.py` e os módulos existentes antes de editar.
- [ ] Criar uma branch ou commit de segurança.
- [ ] Inspecionar `requirements.txt`/versão instalada; confirmar que o Streamlit oferece `st.navigation(..., position="top")` (disponível a partir da versão 1.46).
- [ ] Registrar o comportamento base com uma captura por página.
- [ ] Não alterar `data/`, notebook, nomes de colunas, fórmulas, percentis, valores-p e demais estatísticas.

**Entrega:** versão original preservada e estratégia técnica definida.

### Etapa B — Transformar abas em páginas reais (prioridade máxima)

- [ ] Em `app.py`, substituir `st.tabs` por `st.Page` + `st.navigation(..., position="top")`.
- [ ] Usar funções *sem argumentos* como wrappers para chamar as funções `renderizar` atuais com `df` e `anos` já carregados; ou outra solução mínima equivalente.
- [ ] Chamar `.run()` **uma única vez** para executar a página selecionada.
- [ ] Deixar `st.set_page_config` no entrypoint; manter o carregamento cacheado em `painel/dados.py`.
- [ ] Manter as 3 páginas existentes funcionando, sem criar cópias das visualizações nem alterar seus cálculos.
- [ ] Remover o bloco global `st.sidebar.*` de `app.py` e preparar sua realocação na Etapa C.
- [ ] Evitar duplicação de cabeçalhos: um título geral discreto e um título identificável em cada página.

**Ponto de parada:** executar o Streamlit; testar a navegação entre as três páginas. Se algo falhar, corrigir antes de seguir.

### Etapa C — Reposicionar os filtros da Visão geral

- [ ] Criar uma função `renderizar_com_filtros(df, anos)` ou `filtros_visao_geral(df, anos)` dentro de `painel/visao_geral.py` (ou módulo utilitário enxuto), mantendo o `renderizar(...)` atual.
- [ ] Exibir **Ano**, **Indicador**, **Tipo de oferta** juntos, no topo do conteúdo (usar `st.columns` sem comprimir a tela).
- [ ] Colocar **GRE**, **Município** e **Busca por escola** em um `st.expander("Filtros adicionais")` (recomendação inicial, mais simples e acessível; `st.popover` é opcional).
- [ ] Manter o filtro de município dependente das GREs escolhidas, como no código atual. Tratar seleções antigas que deixem de ser válidas ao mudar a GRE.
- [ ] Garantir que todos os seis filtros continuem aplicando-se aos KPIs, mapa, histograma e tabela **apenas** da Visão geral.
- [ ] Usar `key`s exclusivas por página para evitar conflitos de widgets; decidir se vale preservar estado ao trocar de página e implementar somente se necessário, de modo compatível com a versão instalada.
- [ ] Nenhuma barra lateral com filtros deve aparecer nas páginas Características e IDEB ou Escola.

**Ponto de parada:** conferir os filtros em 2025/IDEB, combinações GRE/município, busca com e sem resultados e navegação de ida e volta.

### Etapa D — Melhorar a hierarquia visual sem redesenhar os gráficos

- [ ] Padronizar cabeçalho: título curto, uma frase de propósito e controles relevantes, nessa ordem.
- [ ] Evitar mostrar descrição longa repetida acima de cada gráfico.
- [ ] Na Visão geral, preservar mapa, cartões, histograma e tabela; rever espaçamento entre seções e legibilidade em telas menores.
- [ ] Em Características e IDEB, preservar os gráficos e a tabela já validados. Reduzir altura excessiva **quando for seguro**, melhorar tamanho dos rótulos, simplificar instruções e manter N, P20/P80, método e avisos de não causalidade visíveis.
- [ ] Incluir breve interpretação descritiva sobre TDI e formação docente, baseada nos valores reais da exportação (sem causalidade); documentar que a proporção de integrais/parciais difere entre grupos.
- [ ] Na Escola, priorizar busca no início; manter ano da ficha próximo aos cartões e indicador do histórico próximo ao gráfico.
- [ ] Preferir `st.columns`, `st.expander`, `st.container`, `st.divider`; evitar CSS/HTML personalizado, componentes de terceiros e efeitos decorativos.
- [ ] Manter cores coerentes: **integral azul, parcial laranja**, sem misturar o significado das cores quando azul/laranja codificar IDEB alto/baixo (legendas sempre explícitas).

**Ponto de parada:** comparar antes/depois por captura de tela; se os ajustes visuais estiverem piorando a usabilidade, reverter o que não agrega valor.

### Etapa E — Testes e integração

- [ ] Navegação superior abre corretamente cada página; não duplica renderização.
- [ ] Nenhum filtro sem função aparece fora da Visão geral.
- [ ] Visão geral preserva os números de referência em 2025: **469 escolas**, **441 com IDEB** sem filtros adicionais.
- [ ] Características e IDEB preserva, em Todas/2025: **P20=3,8**, **P80=4,7**, **99 no grupo baixo**, **107 no grupo alto**; dispersão com **N=441** e correlações das edições **2017, 2019, 2023, 2025**.
- [ ] Testar recortes Só integrais / Só parciais e as tabelas expansíveis.
- [ ] Testar Escola: selecionar uma escola, alterar ano da ficha, indicador do histórico e voltar à Visão geral.
- [ ] Testar filtros sem correspondência e indicadores indisponíveis para determinado ano.
- [ ] Testar localmente (`streamlit run app.py`) e no ambiente de publicação, incluindo largura de notebook/desktop e largura estreita.
- [ ] Nenhum Parquet foi regravado e nenhum resultado estatístico mudou em consequência da refatoração.
- [ ] Mostrar ao usuário resumo dos arquivos alterados e testes realizados; só então avançar para a página Integral × Parcial.

## 4. Arquivos que o Codex pode alterar

**Prováveis:** `app.py`, `painel/visao_geral.py`; eventualmente `painel/caracteristicas_ideb.py` e `painel/escola.py` para apresentação.

**Preservar salvo necessidade demonstrada:** `painel/dados.py`, `painel/config.py`, `painel/mapas.py`, `data/*.parquet`, `data/municipios.geojson`, notebook e cálculos científicos.

**Não fazer nesta tarefa:** criar a página Integral × Parcial; elaborar a página Sobre; recalcular correlações; alterar percentis; trocar o conjunto de indicadores; migrar frameworks; implementar login; reconstruir mapa.

## 5. Critério de conclusão

A reorganização estará concluída quando o usuário conseguir passar entre as três páginas usando o menu superior, encontrar apenas filtros que afetam a tela ativa, entender a finalidade de cada seção e observar os mesmos números e gráficos de antes. Deve ser possível adicionar depois mais duas páginas sem repetir o problema dos filtros globais.

## 6. Pedido pronto para enviar ao Codex

> Leia `PLANO_REORGANIZACAO_INTERFACE_PAINEL_TCC.md` e analise o código existente antes de alterar qualquer arquivo. Quero reorganizar a navegação e os filtros do meu painel Streamlit, preservando os cálculos, Parquets, gráficos e resultados já validados. Trabalhe **por etapas**, começando pelas Etapas A, B e C. Use navegação superior nativa (`st.Page` + `st.navigation(position="top")`) caso a versão instalada ofereça suporte. Remova os filtros globais e faça os filtros da Visão geral aparecerem e atuarem somente nela. Não crie novas páginas e não redesenhe os gráficos neste primeiro momento. Faça alterações pequenas, teste a execução, mostre os arquivos alterados e pare para minha revisão antes da Etapa D. Se houver ambiguidades, priorize preservar o comportamento existente.

## Referências técnicas oficiais

- `st.navigation`: https://docs.streamlit.io/develop/api-reference/navigation/st.navigation
- `st.Page`: https://docs.streamlit.io/develop/api-reference/navigation/st.page
- Widgets em apps multipáginas: https://docs.streamlit.io/develop/concepts/multipage-apps/widgets
- Notas da versão 1.46 (navegação superior): https://docs.streamlit.io/develop/quick-reference/release-notes/2025
