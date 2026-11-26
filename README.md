# Cache em memória e latência de APIs web: análise do TechEmpower Round 23

Projeto final de MCEQ 12576 (PUC-Campinas, 2º sem. 2026). Arthur Sebastian Guarniz de Castro e Lucas Anelli Bissi.

**Pergunta:** em frameworks web que servem leituras de banco de dados, o cache em memória está associado a menor latência média por requisição do que a consulta direta ao banco? Estudo **observacional**, com desenho pareado por framework. O plano completo, registrado antes da análise, está em [PROTOCOLO.md](PROTOCOLO.md).

## Dados
- **Fonte:** [TechEmpower Framework Benchmarks](https://www.techempower.com/benchmarks/), Round 23, hardware físico (UUID `91a66052-9d86-446c-b31a-eadbd669ed08`, commit `523534bb61`). Round 22 usado como réplica exploratória.
- **URL:** `https://www.techempower.com/benchmarks/results/round23/ph.json`. Acesso em 15/11/2026.
- **Licença:** BSD 3-cláusulas ([LICENSE](https://github.com/TechEmpower/FrameworkBenchmarks/blob/master/LICENSE)).
- **Medição:** feita pelos autores originais com o wrk, 15 s por execução, após aquecimento. Os testes comparados são *Multiple queries* (sem cache) e *Cached queries* (com cache), conforme a [especificação](https://github.com/TechEmpower/FrameworkBenchmarks/wiki/Project-Information-Framework-Tests-Overview).

## Como reexecutar
```bash
pip install -r requirements.txt
python baixar_dados.py   # dados/brutos/ (imprime o SHA-256 para conferência)
python limpar.py         # dados/limpos/pares_roundXX.csv e excluidos_roundXX.csv
python analise.py --teste  # autoteste do código com dados sintéticos
python analise.py        # resultados/resultados.json e resultados/figura1.png
```
Os dados brutos nunca são editados à mão; `dados/limpos/` é sempre gerado pelo script.
