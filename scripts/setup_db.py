"""Check PostgreSQL reachability and create the app user/database if missing.

Credentials come from .env (POSTGRES_*). Safe to re-run: it only creates what
is absent and never drops anything.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import psycopg

DB_NAME = os.environ.get("POSTGRES_DB", "compendium")
DB_USER = os.environ.get("POSTGRES_USER", "compendium")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

SUPERUSER = os.environ.get("POSTGRES_SUPERUSER", "postgres")
SUPER_PASSWORD = os.environ.get("POSTGRES_SUPERUSER_PASSWORD", "")


def main() -> int:
    print(f"target: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    # 1. Try the application credentials first.
    try:
        with psycopg.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD, connect_timeout=5,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("select version()")
                print("OK: connected with app credentials")
                print("   ", cur.fetchone()[0][:70])
            return 0
    except psycopg.OperationalError as exc:
        print("app credentials failed:", str(exc).strip().splitlines()[0])
    except Exception as exc:  # noqa: BLE001
        print("app credentials failed:", exc)

    # 2. Fall back to the superuser to provision the role and database.
    if not SUPER_PASSWORD:
        print("\nCannot provision: set POSTGRES_SUPERUSER_PASSWORD in .env")
        return 1

    print(f"\nprovisioning via superuser '{SUPERUSER}' ...")
    try:
        with psycopg.connect(
            host=DB_HOST, port=DB_PORT, dbname="postgres",
            user=SUPERUSER, password=SUPER_PASSWORD, connect_timeout=5,
        ) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "select 1 from pg_roles where rolname = %s", (DB_USER,)
                )
                if cur.fetchone() is None:
                    cur.execute(
                        f'create role "{DB_USER}" login password %s', (DB_PASSWORD,)
                    )
                    print(f"created role {DB_USER}")
                else:
                    print(f"role {DB_USER} already exists")

                cur.execute(
                    "select 1 from pg_database where datname = %s", (DB_NAME,)
                )
                if cur.fetchone() is None:
                    cur.execute(f'create database "{DB_NAME}" owner "{DB_USER}"')
                    print(f"created database {DB_NAME}")
                else:
                    print(f"database {DB_NAME} already exists")
    except Exception as exc:  # noqa: BLE001
        print("provisioning failed:", exc)
        return 1

    # 3. Verify.
    try:
        with psycopg.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD, connect_timeout=5,
        ):
            print("OK: app credentials now work")
            return 0
    except Exception as exc:  # noqa: BLE001
        print("verification failed:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())