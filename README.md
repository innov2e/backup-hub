# Backup Hub (innov2e/backup-hub)

Guida rapida e completa per avviare, configurare e verificare l'applicazione.

## 1) Cos'è questa applicazione

`backup-hub` è un runner Python che:

1. legge una lista di app/oggetti da `control/config/apps.yaml`;
2. scarica record da Knack;
3. salva i dati in JSON compresso (`.json.gz`);
4. carica dati e allegati su storage S3 compatibile (Wasabi).

Il comando principale è:

```bash
./venv/bin/python -m engine.runners.run_backup --all
```

oppure:

```bash
./venv/bin/python -m engine.runners.run_backup --app <nome_app>
```

---

## 2) Prerequisiti

- Python 3.11+ (nel repo è presente un virtualenv Python 3.12 in `venv/`)
- Accesso rete verso:
  - API Knack (`https://api.knack.com/v1`)
  - endpoint S3/Wasabi configurato
- Credenziali valide per Knack e Wasabi

Dipendenze usate dal codice:

- `python-dotenv`
- `PyYAML`
- `requests`
- `boto3` (con `botocore`)

> Nota: il progetto in questo stato non espone un `requirements.txt`; se devi ricreare l'ambiente da zero, installa i pacchetti sopra.

---

## 3) Struttura cartelle importante

```text
backup-hub/
├── control/
│   ├── config/
│   │   ├── apps.yaml
│   │   └── credentials.env
│   └── logs/
├── engine/
│   ├── runners/run_backup.py
│   ├── extractors/knack_extractor.py
│   ├── normalizers/
│   └── common/
└── tmp/
```

### Attenzione al path base

Il runner usa un path **hardcoded**:

- `BASE_DIR = /opt/backup-hub`

Quindi in produzione l'app va mappata in `/opt/backup-hub` (oppure bisogna modificare il codice).

---

## 4) File di configurazione

## 4.1 `control/config/apps.yaml`

Definisce:

- elenco app da processare (`apps`)
- tipo sorgente (`source`, attualmente `knack`)
- nomi delle variabili d'ambiente da leggere per app id e api key
- oggetti Knack da esportare (`objects` con `name` e `object_id`)

Esempio semplificato:

```yaml
apps:
  - name: app_unimarconi
    source: knack
    knack_app_id_env: KNACK_APP_ID_UNIMARCONI
    knack_api_key_env: KNACK_API_KEY_UNIMARCONI
    objects:
      - name: SGCS_Campaigns
        object_id: "object_8"
```

## 4.2 `control/config/credentials.env`

Contiene tutte le variabili sensibili:

- endpoint/bucket/regione Wasabi
- app id e api key Knack per ogni app

Il runner carica questo file automaticamente con `load_dotenv(...)`.

---


## 4.3 Gestione sicura delle credenziali

`credentials.env` contiene segreti applicativi: **non committare chiavi reali** su repository condivisi.

Pratiche consigliate:

- mantenere nel repo solo un file template (es. `credentials.env.example`);
- in produzione usare secret manager o variabili d'ambiente iniettate dal runtime;
- ruotare periodicamente API key Knack e credenziali storage.

---

## 5) Variabili d'ambiente necessarie

## 5.1 Storage S3/Wasabi

Obbligatorie:

- `WASABI_BUCKET`
- `WASABI_ENDPOINT`
- `WASABI_REGION`

## 5.2 Knack (una coppia per ogni app)

Per ogni app definita in `apps.yaml`, devono esistere:

- variabile `KNACK_APP_ID_*`
- variabile `KNACK_API_KEY_*`

Il nome esatto è quello specificato nei campi:

- `knack_app_id_env`
- `knack_api_key_env`

---

## 6) Avvio applicazione

## 6.1 Attiva virtualenv (consigliato)

```bash
source venv/bin/activate
```

## 6.2 Verifica CLI disponibile

```bash
./venv/bin/python -m engine.runners.run_backup --help
```

Output atteso: opzioni `--app APP` oppure `--all`.

## 6.3 Esegui backup di tutte le app

```bash
./venv/bin/python -m engine.runners.run_backup --all
```

## 6.4 Esegui backup di una sola app

Esempio:

```bash
./venv/bin/python -m engine.runners.run_backup --app app_unimarconi
```

Se il nome app non esiste in `apps.yaml`, il processo termina con errore.

---

## 7) Comandi utili di verifica

## 7.1 Verifica configurazioni presenti

```bash
ls control/config
```

Atteso: almeno `apps.yaml` e `credentials.env`.

## 7.2 Verifica app disponibili

```bash
./venv/bin/python - <<'PY'
import yaml
from pathlib import Path
p = Path('control/config/apps.yaml')
cfg = yaml.safe_load(p.read_text(encoding='utf-8'))
print('App configurate:')
for app in cfg.get('apps', []):
    print('-', app.get('name'))
PY
```

## 7.3 Verifica variabili d'ambiente richieste (da file)

```bash
./venv/bin/python - <<'PY'
import yaml
from pathlib import Path

env_path = Path('control/config/credentials.env')
apps_path = Path('control/config/apps.yaml')

# Parse env file semplice (KEY=VALUE)
env = {}
for line in env_path.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    env[k.strip()] = v.strip()

cfg = yaml.safe_load(apps_path.read_text(encoding='utf-8'))
required = {'WASABI_BUCKET', 'WASABI_ENDPOINT', 'WASABI_REGION'}
for app in cfg.get('apps', []):
    required.add(app['knack_app_id_env'])
    required.add(app['knack_api_key_env'])

missing = [k for k in sorted(required) if k not in env or env[k] == '']
if missing:
    print('MANCANTI:')
    for k in missing:
        print('-', k)
    raise SystemExit(1)

print('OK: tutte le variabili richieste sono presenti in credentials.env')
PY
```

## 7.4 Verifica log run

```bash
ls -lh control/logs
```

Durante/dopo un'esecuzione deve comparire un file `run_YYYY-MM-DD.log`.

## 7.5 Verifica output temporanei

```bash
ls -lh tmp
```

I file `.json.gz` vengono creati durante il run prima dell'upload.

---

## 8) Dove finiscono i dati su S3/Wasabi

Chiavi oggetti generate dal runner:

- Dati:
  - `knack/<app_name>/<YYYY-MM-DD>/data/<object_name>.json.gz`
- Allegati:
  - `knack/<app_name>/<YYYY-MM-DD>/attachments/<object_name>/<record_id>/<filename>`

---

## 9) Troubleshooting rapido

- **Errore "App not found in apps.yaml"**
  - Il valore passato a `--app` non corrisponde esattamente a `apps[].name`.
- **Errore variabile ambiente mancante**
  - In `credentials.env` manca una chiave referenziata in `apps.yaml`.
- **Errore upload S3**
  - Verifica endpoint/regione/bucket e connettività rete.
- **Errore chiamate Knack**
  - Verifica `KNACK_APP_ID_*` / `KNACK_API_KEY_*` e accesso API.

---

## 10) Esempio di run completo

```bash
cd /opt/backup-hub
source venv/bin/activate
./venv/bin/python -m engine.runners.run_backup --all
```

Poi controlla:

```bash
tail -n 100 control/logs/run_$(date +%F).log
```

