#!/usr/bin/env bash
# Builds .prg files for the fenix 7 family. Needs the Connect IQ SDK (monkeyc) + device files.
# Usage: ./build.sh <developer_key.der>
set -euo pipefail
KEY="${1:-developer_key.der}"
MONKEYC="$(command -v monkeyc || true)"
if [ -z "$MONKEYC" ]; then
  MONKEYC="$(find / -type f -name monkeyc -path '*bin*' 2>/dev/null | head -1)"
fi
echo "monkeyc: $MONKEYC"
# Make device files visible under $HOME if they live elsewhere
if [ ! -d "$HOME/.Garmin/ConnectIQ/Devices/fenix7" ]; then
  DEV="$(find / -type d -name fenix7 -path '*Devices*' 2>/dev/null | head -1 || true)"
  if [ -n "$DEV" ]; then
    mkdir -p "$HOME/.Garmin/ConnectIQ"
    ln -sfn "$(dirname "$DEV")" "$HOME/.Garmin/ConnectIQ/Devices"
  fi
fi
mkdir -p dist
for d in fenix7 fenix7s fenix7x fenix7pro fenix7spro fenix7xpro; do
  echo "== $d"
  "$MONKEYC" -f monkey.jungle -d "$d" -o "dist/GMT-Master-II-$d.prg" -y "$KEY" -r -w
done
ls -la dist
