# Checklist post-merge su VM Hetzner (`/opt/knack-services/backup-hub`)

Questa checklist serve quando hai già fatto merge su GitHub e devi allineare la VM di produzione Hetzner.

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

## 2) Verifica riferimenti hardcoded al vecchio path

Nel progetto ci sono riferimenti a `/opt/backup-hub` che in produzione Hetzner devono diventare `/opt/knack-services/backup-hub`.

Controllo consigliato:

```bash
cd /opt/knack-services/backup-hub
rg -n "/opt/backup-hub" -g '!venv/**'
```

---

## 3) File da aggiornare (riferimenti path)

## 3.1 File runtime principale (OBBLIGATORIO)

- `engine/runners/run_backup.py`

Da cambiare:

```python
BASE_DIR = Path("/opt/backup-hub")
```

in:

```python
BASE_DIR = Path("/opt/knack-services/backup-hub")
```

> Questo è il file effettivamente usato dal comando `python -m engine.runners.run_backup`.

## 3.2 File documentazione (consigliato)

- `README.md`

Aggiorna i punti dove compare `/opt/backup-hub` per allineare la doc alla produzione Hetzner.

## 3.3 File storici/backup presenti nel repo (solo se davvero usati)

Nel repository esistono anche:

- `engine/runners/run_backup.py.001`
- `engine/runners/run_backup.py.noattachment`
- `engine/runners/run_backup.py.noattachment01`

Contengono lo stesso riferimento al vecchio path. Normalmente non sono usati in produzione, ma:

- se li usi manualmente, aggiorna anche questi;
- se non servono, valuta di archiviarli/rimuoverli per evitare confusione.

---

## 4) Verifica funzionale minima dopo update

Dopo aver aggiornato il path nel runner:

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

## 5) Run operativo

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

## 6) Suggerimento per evitare futuri hardcode

Per evitare di dover cambiare codice a ogni diversa installazione, considera in una PR futura di rendere `BASE_DIR` configurabile via env var, ad esempio:

- `BACKUP_HUB_BASE_DIR=/opt/knack-services/backup-hub`

con fallback a un valore di default.
