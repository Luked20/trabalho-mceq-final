# Protocolo do Projeto Final – MCEQ 12576

**Registrado em:** 15/11/2026 e aprovado pela equipe em 16/11/2026, antes de qualquer análise das latências (só a estrutura e a contagem de pares da base foram inspecionadas).

**EQUIPE / MEMBROS:** Arthur Guarniz Castro Sebastian · Lucas Anelli Bissi

## Campos herdados da Ficha de Hipótese (atualizados)

**PROBLEMA (lacuna):** a recomendação de usar cache em memória para APIs de leitura intensiva se apoia mais em relatos do que em medição sob condições controladas, e o ganho raramente é qualificado pela carga da requisição.

**PERGUNTA DE PESQUISA:** em frameworks web que servem leituras de um banco relacional/documental (contexto), o uso de cache em memória (intervenção) está associado a menor (efeito) latência média por requisição, em ms (métrica), comparado à consulta direta ao banco (baseline)?

**H0:** µ_D = 0 · **H1 (unilateral):** µ_D < 0, com D = latência_cache − latência_sem_cache, por framework.
Justificativa do teste unilateral: a mesma da ficha (o acesso à memória é ordens de grandeza mais rápido que uma consulta ao SGBD).

**VI (fator) e níveis:** cache em memória. A = teste *Cached queries* (biblioteca de cache em processo ou Redis em processo separado); B = teste *Multiple queries* (consulta direta; cache proibido pela especificação).

**VD e unidade:** latência média (`latencyAvg`, medida pelo wrk) por execução, em ms.

**CONTROLE:** mesmo hardware (Citrine), mesmo SGBD de origem, mesma ferramenta de carga, aquecimento descartado, mesmo código de framework (commit `523534bb61`), mesmo N de objetos por requisição nos dois níveis.
**MODERADORA:** número de objetos por requisição, N ∈ {1, 10, 20}.

**O QUE MUDOU EM RELAÇÃO À FICHA:** (1) a R4 proíbe benchmark próprio, então os dados passam a ser públicos (TechEmpower) e não um experimento k6/JMeter da equipe; (2) o estudo passa a ser **observacional**, porque os frameworks não foram sorteados (conclusões em termos de "está associado a"); (3) a unidade é o framework e o desenho é pareado; (4) não dá para usar a moderadora "padrão de acesso (Zipf × uniforme)", que não existe na base, e ela é substituída por N; (5) a intervenção é "cache em memória" em geral, não só Redis.

## Campos novos

**BASE ESCOLHIDA:** TechEmpower Framework Benchmarks, Round 23, hardware físico, "Continuous Benchmarking Run 2025-01-30", UUID `91a66052-9d86-446c-b31a-eadbd669ed08`. URL: `https://www.techempower.com/benchmarks/results/round23/ph.json`. Acesso em 15/11/2026. Licença BSD 3-cláusulas.

**JUSTIFICATIVA DA BASE (Seção 3.2):** proveniência, versão e commit fixos; especificação pública de cada teste; licença permite uso e redistribuição; 119 frameworks com os dois testes; VI e VD presentes diretamente; medição documentada (wrk, 15 s por execução).

**TIPO DE ESTUDO:** observacional (benchmark publicado por terceiros).

**DESENHO:** pareado (cada framework medido nos dois níveis), com 2 tratamentos.

**UNIDADE DE ANÁLISE e n:** framework; n ≈ 119 pares antes das exclusões.
**Exclusões (definidas agora):** o par sai se qualquer lado, no N analisado, não tiver latência, tiver `totalRequests` = 0 ou tiver erro (5xx, timeout, connect, read, write > 0). O número de excluídos será relatado.

**TESTE PREVISTO, α e estatística:** análise confirmatória em **N = 20**. Teste t pareado unilateral sobre D (ms), α = 0,05, estatística = média de D.

**TESTE ALTERNATIVO (se pressupostos falharem):** se Shapiro-Wilk em D der p < 0,05, a decisão passa a ser pelo **Wilcoxon de postos sinalizados** unilateral (os dois serão relatados, mas vale este).

**TAMANHO DE EFEITO E IC:** d_z = média(D)/dp(D) (com o t) ou correlação rank-biserial (com o Wilcoxon). IC 95% da média de D por bootstrap percentil, 10.000 reamostras, `default_rng(2026)`. Também será relatada a mediana de D.

**HIPÓTESE SECUNDÁRIA PLANEJADA (moderadora):** D difere entre N = 1, 10, 20? Teste de Friedman (pareado, k = 3), α = 0,05.

**EXPLORATÓRIO (rotulado como tal no artigo):** réplica no Round 22; recortes por SGBD ou linguagem.

**AMEAÇAS À VALIDADE INICIAIS:**
- **Conclusão:** latência assimétrica e com outliers (mitigação: teste alternativo definido previamente e IC por bootstrap).
- **Interna:** confundimento por framework e por linguagem (o pareamento controla); com cache é permitido buscar os N objetos numa só operação, o que confunde o efeito do cache com o do lote.
- **Construção:** a VD é uma média por execução e não por requisição; "cache" cobre implementações diferentes.
- **Externa:** frameworks otimizados para benchmark, rede local e um único servidor.
