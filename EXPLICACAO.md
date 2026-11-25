# Explicação da análise

Guia para a equipe entender e explicar o trabalho. Os números vêm de `resultados/resultados.json` e de `dados/limpos/`.

## 1. A pergunta

Em frameworks web que leem dados de um banco, o **cache em memória está associado a menor latência média** do que a consulta direta ao banco?

Para cada framework, calculamos a diferença:

> **D = latência com cache − latência sem cache** (em ms)

D negativo significa que a latência foi menor com cache.

| Hipótese | Notação | Significado |
|---|---|---|
| H0 | µ_D = 0 | Não há diferença |
| H1 (unilateral) | µ_D < 0 | A latência é menor com cache |

O teste é unilateral porque a teoria prevê só uma direção: ler da memória é muito mais rápido do que consultar o banco. O nível de significância é **α = 0,05**.

## 2. A escolha do dataset

A ficha original previa um experimento próprio com Redis e k6/JMeter. A regra R4 do roteiro proíbe coleta própria, então passamos a usar dados públicos: o **TechEmpower Framework Benchmarks (TFB), Round 23**, um benchmark aberto que mede muitos frameworks web no mesmo hardware.

| Critério do roteiro | Como o TFB atende |
|---|---|
| Proveniência | Rodada identificada (UUID `91a66052-...`, commit `523534bb61`, execução iniciada em 30/01/2025) |
| Documentação | Especificação pública de cada teste |
| Licença | BSD 3-cláusulas |
| Tamanho | 121 frameworks com os dois testes |
| Variáveis | Os testes com e sem cache e a latência já estão na base |
| Medição | Ferramenta wrk, 15 s por execução, hardware "Citrine" |

Os dados foram acessados em 15/11/2026. O **Round 22** foi usado só como réplica exploratória.

### O que mudou em relação à ficha
- Dados públicos no lugar de um experimento próprio.
- O estudo virou **observacional**: ninguém sorteou tratamentos, então dizemos "está associado a", nunca "causa" ou "reduz".
- A intervenção é cache em memória em geral, não só Redis.
- A moderadora "padrão de acesso" não existe na base e foi trocada por **N**, o número de objetos por requisição.

## 3. As variáveis

| Papel | Variável |
|---|---|
| Independente (VI) | Cache: **com** (teste *Cached queries*) ou **sem** (teste *Multiple queries*) |
| Dependente (VD) | Latência média por execução (`latencyAvg`), em ms |
| Moderadora | N = 1, 10 ou 20 objetos por requisição |
| Controles | Mesmo hardware, ferramenta de carga e framework nos dois lados, e o mesmo N |

## 4. O desenho: pareado

Cada framework aparece **com e sem cache** e é comparado consigo mesmo. Assim, diferenças entre frameworks (linguagem, maturidade etc.) pesam menos na comparação. A unidade de análise é o framework.

A análise principal usa **N = 20**, escolhido no protocolo.

## 5. O caminho dos dados

1. **`baixar_dados.py`** baixa o JSON bruto e imprime o SHA-256.
2. **`limpar.py`** monta os pares, converte us/ms/s para ms e aplica as exclusões.
3. **`analise.py`** roda os testes e gera `resultados.json` e `figura1.png`.

Um par é excluído se qualquer um dos lados não tiver latência, tiver zero requisições ou tiver erros (5xx, timeout, connect, read ou write).

| Round 23, N = 20 | Frameworks |
|---|---|
| Com os dois testes | 121 |
| Excluídos por erros | 8 |
| Excluídos por falta de latência | 2 |
| **Analisados** | **111** |

O protocolo fala em "≈ 119 pares", que corresponde a 121 menos os 2 sem latência.

## 6. Os métodos estatísticos

São **testes de hipótese e medidas de efeito**. Não ajustamos modelos preditivos, como regressão.

| Método | Para que serve | Por que usamos |
|---|---|---|
| Estatística descritiva | Média, mediana, desvio-padrão, p95, mínimo e máximo | Conhecer os dados antes de testar |
| **Shapiro-Wilk** | Verifica se D parece normal | O teste t supõe diferenças aproximadamente normais |
| **t pareado** | Compara a média de D com zero | Era o teste previsto |
| **Wilcoxon de postos sinalizados** | Ordena as diferenças por tamanho e compara positivas e negativas | Alternativa definida no protocolo se Shapiro der p < 0,05 |
| **d_z** | Efeito do teste t: média de D ÷ desvio-padrão de D | Acompanha o t |
| **Rank-biserial** | Efeito do Wilcoxon, de −1 a +1 | −1 significa que todas as diferenças são negativas |
| **Bootstrap percentil** | Reamostra os dados 10.000 vezes (semente 2026) para obter o IC 95% da média de D | Não supõe normalidade |
| **Friedman** | Compara 3 ou mais condições pareadas | Testa se D muda com N = 1, 10 e 20 |

### Como a decisão foi tomada
Shapiro-Wilk deu p ≈ 3 × 10⁻¹⁹, então D **não é normal**. Pela regra do protocolo, **vale o Wilcoxon**. O t também é relatado, mas não decide.

## 7. Os resultados

### 7.1 Hipótese principal (Round 23, N = 20, n = 111)

| Latência (ms) | Com cache | Sem cache | D |
|---|---|---|---|
| Média | 11,86 | 76,96 | −65,10 |
| Mediana | 1,50 | 14,54 | −11,07 |
| Desvio-padrão | 31,31 | 207,11 | 202,46 |
| p95 | 59,28 | 616,98 | 32,88 |
| Mínimo | 0,21 | 4,73 | −1113,47 |
| Máximo | 210,51 | 1150,00 | 191,53 |

| Teste | Estatística | p unilateral | Efeito |
|---|---|---|---|
| **Wilcoxon (decide)** | W = 674 | **4,0 × 10⁻¹³** | rank-biserial = **−0,78** |
| t pareado | t = −3,39 | 4,9 × 10⁻⁴ | d_z = −0,32 |

IC 95% da média de D: **[−105,05; −30,84] ms**.

**Decisão: rejeitamos H0.** A latência foi menor com cache em **100 de 111** frameworks.

### 7.2 Média ou mediana?
A média de D (−65 ms) é puxada por sete frameworks com D entre −563 e −1113 ms. A mediana (**−11 ms**) descreve melhor o framework típico. Por isso relatamos as duas.

### 7.3 Quando o cache não foi melhor
Em **11 frameworks** a latência foi maior com cache, incluindo quatro variantes do officefloor. O pior caso foi o cfml-adobe (+191,53 ms). A base não permite dizer o motivo.

### 7.4 Moderadora N (secundária, planejada)
Entram os 110 frameworks válidos nos três valores de N.

| N | Mediana de D (ms) |
|---|---|
| 1 | −0,77 |
| 10 | −6,47 |
| 20 | −11,15 |

Friedman: χ² = 129,84; p = 6,4 × 10⁻²⁹. **D difere conforme N**, e a mediana fica mais negativa com mais objetos. O teste não diz quais pares de N diferem, pois não fizemos pós-teste.

A mediana em N = 20 muda um pouco (−11,15 em vez de −11,07) porque aqui são 110 frameworks, e não 111.

### 7.5 Réplica no Round 22 (exploratória)
São 98 pares, após excluir 14 de 112.

| Medida | Valor |
|---|---|
| Média de D | −29,81 ms |
| IC 95% da média | [−53,95; −1,00] ms |
| Mediana de D | −26,16 ms |
| Wilcoxon | p = 3,1 × 10⁻¹¹ |
| Rank-biserial | −0,76 |

O resultado vai na mesma direção, mas não é confirmação independente: muitos frameworks se repetem entre as rodadas.

## 8. Limitações

- **Conclusão:** dados assimétricos e com valores extremos. H0 fala da média, mas o Wilcoxon trabalha com postos (e supõe diferenças simétricas para falar do centro de D). Variantes do mesmo framework, como trillium e officefloor, não são totalmente independentes, então o p-valor pode estar otimista.
- **Interna:** o estudo é observacional. Com cache, é permitido buscar os N objetos de uma vez, o que mistura o efeito do cache com o do lote.
- **Construção:** a VD é a média de cada execução, não a latência de cada requisição. "Cache" reúne implementações diferentes. A latência também pode refletir a vazão sob carga alta.
- **Externa:** os frameworks são otimizados para benchmark, em rede local e um único servidor. Uma aplicação real pode se comportar de outra forma.

## 9. Resumo em uma frase

No TFB Round 23, com N = 20, o cache em memória **está associado** a menor latência (Wilcoxon, p = 4,0 × 10⁻¹³; rank-biserial = −0,78; mediana de D = −11 ms), mas o tamanho da diferença varia muito entre frameworks e o estudo **não permite afirmar causa**.
