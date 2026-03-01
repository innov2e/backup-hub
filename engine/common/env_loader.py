from pathlib import Path
import os


def load_env_file(path: Path) -> None:
    """
    Carica variabili ambiente da file .env in formato KEY=VALUE.

    Regole supportate:
    - righe vuote/commenti (#) ignorati
    - coppie KEY=VALUE
    - valore opzionalmente quotato con "..." o '...'
    - non sovrascrive variabili già presenti in environment
    """
    p = Path(path)
    if not p.exists():
        return

    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ('"', "'")
        ):
            value = value[1:-1]

        if key not in os.environ:
            os.environ[key] = value
