"""
Análise estatística das medições de RSSI (TCC - Blindagem eletromagnética passiva, 2,4 GHz)

Uso:
    pip install pandas scipy
    python3 analise_rssi.py pasta_com_os_csv

Lê todos os arquivos rssi_*.csv gerados pelo coleta.sh, aplica as exclusões
declaradas em EXCLUSOES, e imprime:
    - estatística descritiva por condição (média, DP, mediana, mín., máx.)
    - contagem de leituras censuradas (sem associação ao roteador)
    - teste de normalidade de Shapiro-Wilk
    - teste de Mann-Whitney de cada condição contra a REF
    - SE = média(REF) - média(condição), conforme a Equação 2 do artigo
Também salva um resumo em resumo_rssi.csv na mesma pasta.
"""

import sys
from pathlib import Path

import pandas as pd
from scipy import stats

# Exclusões declaradas no artigo: condição -> última amostra válida.
# COBRE: aparelho manipulado a partir da amostra 17 (fim da janela antecipado).
EXCLUSOES = {"COBRE": 16}

ALFA = 0.05
REFERENCIA = "REF"


def carregar(pasta: Path) -> pd.DataFrame:
    arquivos = sorted(pasta.glob("rssi_*.csv"))
    if not arquivos:
        sys.exit(f"Nenhum rssi_*.csv encontrado em {pasta}")
    df = pd.concat([pd.read_csv(a) for a in arquivos], ignore_index=True)
    for cond, ultima in EXCLUSOES.items():
        mascara = (df["condicao"] == cond) & (df["amostra"] > ultima)
        if mascara.any():
            print(f"[exclusão] {cond}: removidas {mascara.sum()} leituras após a amostra {ultima}")
        df = df[~mascara]
    return df


def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    df = carregar(pasta)

    ref = df.loc[(df["condicao"] == REFERENCIA) & (df["censurado"] == 0), "rssi_dbm"]
    linhas = []

    for cond, g in df.groupby("condicao", sort=False):
        validos = g.loc[g["censurado"] == 0, "rssi_dbm"].astype(float)
        linha = {
            "condicao": cond,
            "n_total": len(g),
            "n_validos": len(validos),
            "n_censurados": int(g["censurado"].sum()),
        }
        print(f"\n=== {cond} ===")
        print(f"leituras: {len(g)} | válidas: {len(validos)} | censuradas: {linha['n_censurados']}")

        if len(validos) == 0:
            print("Todas censuradas: SE só pode ser expressa como limite inferior "
                    "(média REF - limiar de associação).")
            linhas.append(linha)
            continue

        linha.update(
            media=validos.mean(), dp=validos.std(ddof=1), mediana=validos.median(),
            minimo=validos.min(), maximo=validos.max(),
        )
        print(f"média {linha['media']:.2f} dBm | DP {linha['dp']:.2f} dB | "
                f"mediana {linha['mediana']:.1f} | mín {linha['minimo']:.0f} | máx {linha['maximo']:.0f}")

        if len(validos) >= 3:
            w, p = stats.shapiro(validos)
            linha.update(shapiro_W=w, shapiro_p=p)
            print(f"Shapiro-Wilk: W = {w:.3f}, p = {p:.2g} -> "
                    f"{'rejeita' if p < ALFA else 'não rejeita'} normalidade (α = {ALFA})")

        if cond != REFERENCIA and len(ref) > 0:
            u, p = stats.mannwhitneyu(ref, validos, alternative="two-sided")
            se = ref.mean() - validos.mean()
            linha.update(mannwhitney_U=u, mannwhitney_p=p, SE_dB=se)
            print(f"Mann-Whitney vs {REFERENCIA}: U = {u:.1f}, p = {p:.2g}")
            print(f"SE = média(REF) - média({cond}) = {se:.2f} dB")

        linhas.append(linha)

    saida = pasta / "resumo_rssi.csv"
    pd.DataFrame(linhas).to_csv(saida, index=False, float_format="%.4f")
    print(f"\nResumo salvo em {saida}")


if __name__ == "__main__":
    main()
