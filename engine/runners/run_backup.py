import os
import sys
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from engine.common.env_loader import load_env_file
from engine.common.logger import get_logger
from engine.extractors.knack_extractor import KnackExtractor
from engine.normalizers.json_normalizer import write_json_gz
from engine.common.s3_uploader import S3Uploader
from engine.normalizers.attachment_handler import (
    extract_asset_urls,
    download_asset_from_url
)

# ---------------------------------------------------------
# Costanti
# ---------------------------------------------------------

DEFAULT_BASE_DIR = Path("/opt/backup-hub")
BASE_DIR = Path(os.environ.get("BACKUP_HUB_BASE_DIR", str(DEFAULT_BASE_DIR)))
TMP_DIR = BASE_DIR / "tmp"


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Backup Hub – Knack Backup Runner"
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--app",
        help="Esegue il backup della sola app indicata (name in apps.yaml)"
    )

    group.add_argument(
        "--all",
        action="store_true",
        help="Esegue il backup di tutte le app"
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    args = parse_args()

    # -----------------------------------------------------
    # Env + logger
    # -----------------------------------------------------

    load_env_file(BASE_DIR / "control/config/credentials.env")

    logger = get_logger(str(BASE_DIR / "control/logs"))
    logger.info("=== BACKUP RUN START ===")

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    # Config
    # -----------------------------------------------------

    with open(BASE_DIR / "control/config/apps.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    apps_cfg = cfg.get("apps", [])

    if args.app:
        apps_cfg = [a for a in apps_cfg if a.get("name") == args.app]
        if not apps_cfg:
            logger.error(f"App not found in apps.yaml: {args.app}")
            sys.exit(1)

    # -----------------------------------------------------
    # S3 / Wasabi
    # -----------------------------------------------------

    wasabi_access_key = (
        os.environ.get("WASABI_ACCESS_KEY")
        or os.environ.get("AWS_ACCESS_KEY_ID")
    )
    wasabi_secret_key = (
        os.environ.get("WASABI_SECRET_KEY")
        or os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    wasabi_session_token = os.environ.get("AWS_SESSION_TOKEN")

    if not (wasabi_access_key and wasabi_secret_key):
        logger.warning(
            "No explicit S3 credentials found in env "
            "(WASABI_ACCESS_KEY/WASABI_SECRET_KEY or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY). "
            "Falling back to boto3 default credential chain."
        )

    s3 = S3Uploader(
        endpoint_url=os.environ["WASABI_ENDPOINT"],
        region=os.environ["WASABI_REGION"],
        bucket=os.environ["WASABI_BUCKET"],
        logger=logger,
        access_key_id=wasabi_access_key,
        secret_access_key=wasabi_secret_key,
        session_token=wasabi_session_token,
    )

    run_date = datetime.now().strftime("%Y-%m-%d")

    # -----------------------------------------------------
    # Loop APP
    # -----------------------------------------------------

    for app in apps_cfg:

        if app.get("source") != "knack":
            logger.info(f"SKIP non-knack app: {app.get('name')}")
            continue

        app_name = app["name"]
        logger.info(f"Processing app: {app_name}")

        app_id = os.environ[app["knack_app_id_env"]]
        api_key = os.environ[app["knack_api_key_env"]]

        extractor = KnackExtractor(
            app_id=app_id,
            api_key=api_key,
            logger=logger
        )

        # -------------------------------------------------
        # Loop OBJECT
        # -------------------------------------------------

        for obj in app.get("objects", []):
            obj_name = obj["name"]
            object_id = obj["object_id"]

            logger.info(f"Processing object: {obj_name}")

            # 1️⃣ Extract records
            records = extractor.fetch_all_records(object_id=object_id)

            # 2️⃣ Write JSON locally
            local_json = TMP_DIR / f"{obj_name}.json.gz"
            write_json_gz(str(local_json), records)

            # 3️⃣ Upload JSON
            s3_key_json = (
                f"knack/{app_name}/{run_date}/data/{obj_name}.json.gz"
            )
            s3.upload_file(str(local_json), s3_key_json)

            # -------------------------------------------------
            # 4️⃣ Attachments (URL-based)
            # -------------------------------------------------

            assets_count = 0

            for record in records:
                record_id = record.get("id")

                assets = extract_asset_urls(record)

                for asset in assets:
                    tmp_file = None
                    try:
                        asset_url = asset["url"]
                        filename = Path(
                            urlparse(asset_url).path
                        ).name

                        tmp_file = TMP_DIR / filename

                        download_asset_from_url(
                            asset_url,
                            tmp_file
                        )

                        s3_key_asset = (
                            f"knack/{app_name}/{run_date}/attachments/"
                            f"{obj_name}/{record_id}/{filename}"
                        )

                        s3.upload_file(
                            str(tmp_file),
                            s3_key_asset
                        )

                        assets_count += 1

                        logger.info(
                            f"Asset saved: app={app_name}, object={obj_name}, "
                            f"record={record_id}, field={asset['field']}, "
                            f"file={filename}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Asset error app={app_name}, object={obj_name}, "
                            f"record={record_id}, url={asset.get('url')}: {e}"
                        )

                    finally:
                        if tmp_file and tmp_file.exists():
                            tmp_file.unlink()

            logger.info(
                f"Assets backed up: {assets_count} "
                f"(app={app_name}, object={obj_name})"
            )

    logger.info("=== BACKUP RUN END ===")


# ---------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
