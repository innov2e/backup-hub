import logging
from pathlib import Path
from datetime import datetime

def get_logger(log_dir: str, name: str = "backup-hub") -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        ts = datetime.now().strftime("%Y-%m-%d")
        fh = logging.FileHandler(Path(log_dir) / f"run_{ts}.log")
        sh = logging.StreamHandler()

        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh.setFormatter(fmt)
        sh.setFormatter(fmt)

        logger.addHandler(fh)
        logger.addHandler(sh)

    return logger
