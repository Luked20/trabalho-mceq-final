"""dados/brutos/roundXX_ph.json -> dados/limpos/pares_roundXX.csv (um par framework x N por linha).

Regras de exclusão: as do PROTOCOLO.md. Não calcula nenhum teste.
"""
import csv
import json
import pathlib

RAIZ = pathlib.Path(__file__).parent
UNIDADES_MS = {"us": 1e-3, "ms": 1.0, "s": 1e3, "m": 60e3}
ERROS = ("5xx", "timeout", "connect", "read", "write")


def para_ms(txt):
    """'216.45us' -> 0.21645 ; '1.17ms' -> 1.17 ; '2.5s' -> 2500.0"""
    for u in ("us", "ms", "s", "m"):  # ordem importa: 'ms'/'us' antes de 's'/'m'
        if txt.endswith(u):
            return float(txt[: -len(u)]) * UNIDADES_MS[u]
    raise ValueError(txt)


def motivo_exclusao(e):
    if not e or not e.get("latencyAvg"):
        return "sem latencia"
    if not e.get("totalRequests"):
        return "zero requisicoes"
    if any(e.get(k) for k in ERROS):
        return "erros"
    return None


def limpar(rodada):
    d = json.loads((RAIZ / "dados" / "brutos" / f"round{rodada}_ph.json").read_text(encoding="utf8"))
    meta = {m["name"]: m for m in d["testMetadata"]}
    q, c = d["rawData"]["query"], d["rawData"]["cached-query"]
    linhas, excluidos = [], []
    for fw in sorted(set(q) & set(c)):
        for n in (1, 10, 20):
            eq = q[fw][d["queryIntervals"].index(n)]
            ec = c[fw][d["cachedQueryIntervals"].index(n)]
            motivo = motivo_exclusao(eq) or motivo_exclusao(ec)
            if motivo:
                excluidos.append((fw, n, motivo))
                continue
            m = meta.get(fw, {})
            linhas.append({
                "framework": fw, "N": n,
                "linguagem": m.get("language"), "banco": m.get("database"),
                "classificacao": m.get("classification"),
                "lat_sem_cache_ms": para_ms(eq["latencyAvg"]),
                "lat_cache_ms": para_ms(ec["latencyAvg"]),
            })
    saida = RAIZ / "dados" / "limpos" / f"pares_round{rodada}.csv"
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    with (saida.parent / f"excluidos_round{rodada}.csv").open("w", newline="", encoding="utf8") as f:
        csv.writer(f).writerows([("framework", "N", "motivo"), *excluidos])
    for n in (1, 10, 20):
        print(f"round {rodada} N={n}: {sum(l['N'] == n for l in linhas)} pares, "
              f"{sum(x[1] == n for x in excluidos)} excluidos")


if __name__ == "__main__":
    assert para_ms("216.45us") == 0.21645 and para_ms("1.17ms") == 1.17 and para_ms("2.5s") == 2500.0
    for r in (23, 22):
        limpar(r)
