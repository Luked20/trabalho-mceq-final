"""Baixa os resultados brutos do TechEmpower (Round 23 = confirmatório, Round 22 = réplica exploratória)."""
import hashlib
import pathlib
import urllib.request

URL = "https://www.techempower.com/benchmarks/results/round{r}/ph.json"
DEST = pathlib.Path(__file__).parent / "dados" / "brutos"

if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    for r in (23, 22):
        arq = DEST / f"round{r}_ph.json"
        if not arq.exists():
            urllib.request.urlretrieve(URL.format(r=r), arq)
        print(arq.name, hashlib.sha256(arq.read_bytes()).hexdigest())
