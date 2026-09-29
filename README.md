## Análise estatística das medições de RSSI (TCC - Blindagem eletromagnética passiva, 2,4 GHz)

### Uso:
    pip install pandas scipy
    python3 analise_rssi.py pasta_com_os_csv
Lê todos os arquivos rssi_*.csv gerados pelo coleta.sh, aplica as exclusões
declaradas em EXCLUSOES, e imprime:
<ul>
  <li>estatística descritiva por condição (média, DP, mediana, mín., máx.)</li>
  <li>contagem de leituras censuradas (sem associação ao roteador)</li>
  <li>teste de normalidade de Shapiro-Wilk</li>
  <li>teste de Mann-Whitney de cada condição contra a REF</li>
  <li>SE = média(REF) - média(condição), conforme a Equação 2 do artigo</li>
</ul>

#### Também salva um resumo em resumo_rssi.csv na mesma pasta.
