import json
import gzip
from pathlib import Path
from typing import Any

def write_json_gz(path: str, payload: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
