import re
import requests
from pathlib import Path
from typing import List, Dict


# ---------------------------------------------------------
# Regex per estrazione URL da HTML Knack
# ---------------------------------------------------------

# <img src="https://...">
_IMG_SRC_REGEX = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)

# <a href="https://..."> oppure <a ... data-asset-id="...">
_A_HREF_REGEX = re.compile(r'<a[^>]+href="([^"]+)"', re.IGNORECASE)


# ---------------------------------------------------------
# Estrazione asset (URL pubblici) dai record Knack
# ---------------------------------------------------------

def extract_asset_urls(record: Dict) -> List[Dict]:
    """
    Estrae gli URL pubblici degli asset Knack da un record.

    Supporta:
    - Image: <img src="URL">
    - File:  <a href="URL">

    Restituisce una lista di dict:
    {
        type: "image" | "file",
        url: str,
        field: str
    }
    """
    assets = []

    for field, value in record.items():
        if not isinstance(value, str):
            continue

        # -------- Image --------
        img_match = _IMG_SRC_REGEX.search(value)
        if img_match:
            assets.append({
                "type": "image",
                "url": img_match.group(1),
                "field": field
            })
            continue

        # -------- File --------
        link_match = _A_HREF_REGEX.search(value)
        if link_match:
            assets.append({
                "type": "file",
                "url": link_match.group(1),
                "field": field
            })

    return assets


# ---------------------------------------------------------
# Download asset da URL pubblico
# ---------------------------------------------------------

def download_asset_from_url(
    url: str,
    target_path: Path,
    timeout: int = 30
):
    """
    Scarica un asset Knack utilizzando l'URL pubblico
    (lo stesso usato dal browser).

    - nessuna autenticazione richiesta
    - supporta redirect
    - salva il binario così com'è
    """

    with requests.get(
        url,
        stream=True,
        allow_redirects=True,
        timeout=timeout
    ) as response:

        response.raise_for_status()

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
