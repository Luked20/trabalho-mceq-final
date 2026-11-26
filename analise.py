"""Análise confirmatória conforme PROTOCOLO.md.

    python analise.py          -> roda nos dados reais (dados/limpos/), grava em resultados/
    python analise.py --teste  -> autoteste com dados sintéticos (não lê os dados reais)

D = latência_cache - latência_sem_cache (ms), por framework. H1: média(D) < 0.
"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

RAIZ = pathlib.Path(__file__).parent
ALFA = 0.05
N_CONFIRMATORIO = 20
SEMENTE = 2026
N_BOOT = 10_000


def descritiva(x):
    return {"n": int(len(x)), "media": float(np.mean(x)), "mediana": float(np.median(x)),
            "dp": float(np.std(x, ddof=1)), "p95": float(np.percentile(x, 95)),
            "min": float(np.min(x)), "max": float(np.max(x))}


def ic_bootstrap_media(d, rng):
    medias = rng.choice(d, size=(N_BOOT, len(d)), replace=True).mean(axis=1)
    return [float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))]


def hipotese_principal(df, n=N_CONFIRMATORIO):
    sub = df[df["N"] == n]
    a, b = sub["lat_cache_ms"].to_numpy(), sub["lat_sem_cache_ms"].to_numpy()
    d = a - b
    shapiro_p = float(stats.shapiro(d).pvalue)
    t = stats.ttest_rel(a, b, alternative="less")
    w = stats.wilcoxon(a, b, alternative="less")
    # correlação rank-biserial pareada: (W+ - W-) / soma total dos postos
    postos = stats.rankdata(np.abs(d[d != 0]))
    w_pos, w_neg = postos[d[d != 0] > 0].sum(), postos[d[d != 0] < 0].sum()
    usa_wilcoxon = shapiro_p < ALFA
    p_decisao = float(w.pvalue if usa_wilcoxon else t.pvalue)
    return {
        "N": n, "n_pares": int(len(d)),
        "descritiva_cache_ms": descritiva(a), "descritiva_sem_cache_ms": descritiva(b),
        "descritiva_D_ms": descritiva(d),
        "shapiro_D_p": shapiro_p,
        "t_pareado": {"t": float(t.statistic), "p_unilateral": float(t.pvalue),
                      "d_z": float(d.mean() / d.std(ddof=1))},
        "wilcoxon": {"W": float(w.statistic), "p_unilateral": float(w.pvalue),
                     "rank_biserial": float((w_pos - w_neg) / (w_pos + w_neg))},
        "ic95_media_D_ms_bootstrap": ic_bootstrap_media(d, np.random.default_rng(SEMENTE)),
        "teste_da_decisao": "wilcoxon" if usa_wilcoxon else "t_pareado",
        "p_decisao": p_decisao,
        "rejeita_H0": p_decisao < ALFA,
    }


def moderadora_friedman(df):
    df = df.assign(D=df["lat_cache_ms"] - df["lat_sem_cache_ms"])
    tab = df.pivot(index="framework", columns="N", values="D").dropna()
    r = stats.friedmanchisquare(*(tab[c] for c in sorted(tab.columns)))
    return {"n_frameworks": int(len(tab)), "chi2": float(r.statistic), "p": float(r.pvalue),
            "mediana_D_por_N_ms": {int(c): float(tab[c].median()) for c in tab.columns},
            "rejeita_H0": float(r.pvalue) < ALFA}


def figura(df, res, caminho):
    sub = df[df["N"] == N_CONFIRMATORIO]
    d = np.sort((sub["lat_cache_ms"] - sub["lat_sem_cache_ms"]).to_numpy())
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.5, 6.4))  # cabe numa coluna do artigo
    ax1.boxplot([sub["lat_sem_cache_ms"], sub["lat_cache_ms"]], showfliers=True)
    ax1.set_xticks([1, 2], ["Sem cache\n(Multiple queries)", "Com cache\n(Cached queries)"])
    ax1.set_yscale("log")
    ax1.set_ylabel("Latência média (ms, escala log)")
    ax1.set_title(f"(a) Latência por condição, N={N_CONFIRMATORIO}, n={len(sub)}", fontsize=10)
    ax2.plot(d, np.arange(len(d)), "o", ms=3, color="tab:blue")
    lo, hi = res["ic95_media_D_ms_bootstrap"]
    ax2.axvline(0, color="black", lw=0.8)
    ax2.axvline(d.mean(), color="tab:red", label=f"média D = {d.mean():.1f} ms")
    ax2.axvspan(lo, hi, color="tab:red", alpha=0.2, label=f"IC95% [{lo:.1f}; {hi:.1f}]")
    ax2.set_xlabel("D = com cache − sem cache (ms)")
    ax2.set_ylabel("Frameworks (ordenados por D)")
    ax2.set_title("(b) Diferença pareada por framework", fontsize=10)
    ax2.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def rodar(rodada):
    return pd.read_csv(RAIZ / "dados" / "limpos" / f"pares_round{rodada}.csv")


def autoteste():
    rng = np.random.default_rng(0)
    base = rng.lognormal(3, 1, 100)
    linhas = [{"framework": f"fw{i}", "N": n, "lat_sem_cache_ms": base[i] * (1 + n / 20),
               "lat_cache_ms": base[i] * 0.3 * rng.lognormal(0, 0.1)}
              for i in range(100) for n in (1, 10, 20)]
    df = pd.DataFrame(linhas)
    r = hipotese_principal(df)
    assert r["n_pares"] == 100 and r["rejeita_H0"] and r["descritiva_D_ms"]["media"] < 0
    lo, hi = r["ic95_media_D_ms_bootstrap"]
    assert lo < r["descritiva_D_ms"]["media"] < hi < 0
    assert -1 <= r["wilcoxon"]["rank_biserial"] <= -0.9  # quase todos D < 0
    # sem efeito: não deve rejeitar
    nulo = df.assign(lat_cache_ms=df["lat_sem_cache_ms"] * rng.lognormal(0, 0.05, len(df)))
    assert not hipotese_principal(nulo)["rejeita_H0"]
    assert moderadora_friedman(df)["rejeita_H0"]  # efeito cresce com N por construção
    print("autoteste ok")


if __name__ == "__main__":
    if "--teste" in sys.argv:
        autoteste()
        sys.exit()
    out = RAIZ / "resultados"
    out.mkdir(exist_ok=True)
    df23 = rodar(23)
    res = {"confirmatorio": {"round": 23, "hipotese_principal": hipotese_principal(df23),
                             "moderadora_N_friedman": moderadora_friedman(df23)},
           "EXPLORATORIO": {"round22_replica": hipotese_principal(rodar(22))}}
    figura(df23, res["confirmatorio"]["hipotese_principal"], out / "figura1.png")
    (out / "resultados.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(res, indent=2, ensure_ascii=False))
