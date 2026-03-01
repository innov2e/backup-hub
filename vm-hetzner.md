# Checklist post-merge su VM Hetzner (`/opt/knack-services/backup-hub`)

Questa checklist serve quando hai già fatto merge su GitHub e devi allineare la VM di produzione Hetzner.

## 0) Blocco unico copy/paste (update + deps + check E2E)

> Esegui questo blocco direttamente sulla VM Hetzner.

```bash
set -euo pipefail

cd /opt/knack-services/backup-hub

echo "== GIT UPDATE =="
git fetch --all --prune
git checkout main
git pull --ff-only origin main

echo "== VENV + DEPS =="
./venv/bin/python -V
./venv/bin/pip install -r requirements.txt

echo "== SET BASE DIR FOR HETZNER =="
export BACKUP_HUB_BASE_DIR=/opt/knack-services/backup-hub
echo "BACKUP_HUB_BASE_DIR=$BACKUP_HUB_BASE_DIR"

echo "== CONFIG FILE CHECK =="
test -f control/config/apps.yaml
test -f control/config/credentials.env
ls -l control/config/apps.yaml control/config/credentials.env


echo "== S3 CREDENTIALS CHECK =="
./venv/bin/python - <<'PY'
import os
missing = []
if not (os.getenv('WASABI_ACCESS_KEY') or os.getenv('AWS_ACCESS_KEY_ID')):
    missing.append('WASABI_ACCESS_KEY or AWS_ACCESS_KEY_ID')
if not (os.getenv('WASABI_SECRET_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY')):
    missing.append('WASABI_SECRET_KEY or AWS_SECRET_ACCESS_KEY')
if missing:
    print('MISSING:', ', '.join(missing))
    raise SystemExit(1)
print('OK: S3 credentials present in env')
PY

echo "== CLI SMOKE TEST =="
./venv/bin/python -m engine.runners.run_backup --help

echo "== E2E RUN (ALL APPS) =="
./venv/bin/python -m engine.runners.run_backup --all

echo "== LOG TAIL =="
ls -lh control/logs
tail -n 120 control/logs/run_$(date +%F).log
```

> Se vuoi un primo test meno impattante, sostituisci `--all` con `--app app_unimarconi`.

---

## 1) Aggiorna il clone in produzione

```bash
cd /opt/knack-services/backup-hub

git status
git fetch --all --prune
git checkout main
git pull --ff-only origin main
```

Verifica rapida:

```bash
git rev-parse --short HEAD
ls -l README.md
```

---


## 1.1 Dipendenze Python (se il venv è nuovo o incompleto)

```bash
cd /opt/knack-services/backup-hub
./venv/bin/pip install -r requirements.txt
```

> Se vedi errori tipo `ModuleNotFoundError`, verifica sempre che i pacchetti siano installati nel venv corretto.
> Se vedi `NoCredentialsError`, verifica che `WASABI_ACCESS_KEY` e `WASABI_SECRET_KEY` siano valorizzate in `control/config/credentials.env`.

---

## 2) Configura il base path su Hetzner (senza patch codice)

Il runner supporta la variabile ambiente `BACKUP_HUB_BASE_DIR`. Su Hetzner imposta:

```bash
export BACKUP_HUB_BASE_DIR=/opt/knack-services/backup-hub
```

Verifica valore:

```bash
echo "$BACKUP_HUB_BASE_DIR"
```

---

## 3) Verifica funzionale minima dopo update

Dopo aver impostato `BACKUP_HUB_BASE_DIR`:

```bash
cd /opt/knack-services/backup-hub
./venv/bin/python -m engine.runners.run_backup --help
```

Output atteso: opzioni `--app APP` oppure `--all`.

Verifica configurazioni nel path corretto:

```bash
ls -l /opt/knack-services/backup-hub/control/config/apps.yaml
ls -l /opt/knack-services/backup-hub/control/config/credentials.env
```

---

## 4) Run operativo

Singola app:

```bash
cd /opt/knack-services/backup-hub
./venv/bin/python -m engine.runners.run_backup --app app_unimarconi
```

Tutte le app:

```bash
cd /opt/knack-services/backup-hub
./venv/bin/python -m engine.runners.run_backup --all
```

Controllo log:

```bash
ls -lh /opt/knack-services/backup-hub/control/logs
tail -n 100 /opt/knack-services/backup-hub/control/logs/run_$(date +%F).log
```

---

## 5) Nota tecnica

`BASE_DIR` è ora configurabile via `BACKUP_HUB_BASE_DIR`, con fallback al default `/opt/backup-hub`.
