#!/data/data/com.termux/files/usr/bin/bash
# Coleta de RSSI - TCC Blindagem Eletromagnetica Passiva 2,4 GHz
# Uso:  ./coleta.sh CONDICAO REPETICAO [DURACAO_s] [INTERVALO_s] [ESPERA_s]
# Ex.:  ./coleta.sh REF 1 120 2 20
# Saida: ~/storage/downloads/tcc_rssi/rssi_<COND>_r<REP>_<data>.csv

set -u

BSSID_ALVO="1c:7e:e5:c1:a0:14"   # MAC do roteador de teste (conferir!)

COND="${1:?Informe a condicao (ex.: REF, CTRL, BLIND)}"
REP="${2:?Informe o numero da repeticao}"
DURACAO="${3:-120}"   # segundos de coleta
INTERVALO="${4:-2}"   # segundos entre leituras
ESPERA="${5:-20}"     # segundos para fechar a capa e se afastar

DIR="$HOME/storage/downloads/tcc_rssi"
mkdir -p "$DIR"
ARQ="$DIR/rssi_${COND}_r${REP}_$(date +%Y%m%d_%H%M%S).csv"

echo "timestamp,epoch,condicao,repeticao,amostra,rssi_dbm,link_mbps,freq_mhz,bssid,estado,censurado" > "$ARQ"

termux-wake-lock
trap 'termux-wake-unlock' EXIT

echo "Condicao=$COND rep=$REP | inicio em ${ESPERA}s. Posicione o aparelho e afaste-se."
termux-vibrate -d 300 2>/dev/null
sleep "$ESPERA"
termux-vibrate -d 300 2>/dev/null

FIM=$(( $(date +%s) + DURACAO ))
N=0
while [ "$(date +%s)" -lt "$FIM" ]; do
  N=$((N+1))
  LINHA=$(timeout 10 termux-wifi-connectioninfo 2>/dev/null \
    | jq -r '[.rssi, .link_speed_mbps, .frequency_mhz, .bssid, .supplicant_state] | @tsv' 2>/dev/null)
  IFS=$'\t' read -r RSSI LINK FREQ BSS EST <<< "$LINHA"

  # Censurado: desconectado, em outro roteador, ou RSSI invalido
  CENS=0
  if [ "${EST:-}" != "COMPLETED" ] || [ "${BSS:-}" != "$BSSID_ALVO" ] \
     || [ -z "${RSSI:-}" ] || [ "${RSSI:-}" = "null" ] || [ "$RSSI" -le -127 ]; then
    CENS=1
    RSSI=""
  fi

  echo "$(date -Iseconds),$(date +%s),$COND,$REP,$N,$RSSI,${LINK:-},${FREQ:-},${BSS:-},${EST:-SEM_RESPOSTA},$CENS" >> "$ARQ"
  sleep "$INTERVALO"
done

termux-vibrate -d 1000 2>/dev/null
echo "Concluido: $N amostras -> $ARQ"
awk -F, 'NR>1 && $11==0 {s+=$6; n++} NR>1 && $11==1 {c++}
  END { if (n) printf "Media RSSI: %.2f dBm (n=%d) | censuradas: %d\n", s/n, n, c+0;
        else printf "Todas as %d amostras censuradas\n", c }' "$ARQ"
