"""Offline status, replay and streaming export. Never sends messages itself."""

import argparse
import json
from src.service.store import Store


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "retry", "export"])
    parser.add_argument("--table", choices=["inbox", "outbox"], default="inbox")
    parser.add_argument("--source")
    parser.add_argument("--id")
    args = parser.parse_args()
    store = Store()
    if args.command == "status":
        print(json.dumps(store.status(), indent=2))
    elif args.command == "export":
        with store.connect() as db:
            for row in db.execute(
                "SELECT source,id,payload,status,error,created FROM inbox"
            ):
                print(json.dumps(dict(row), ensure_ascii=False))
    else:
        if not args.source or not args.id:
            parser.error(
                "retry requires --source and --id; inspect and fix the cause first"
            )
        key = "id" if args.table == "inbox" else "ad_id"
        with store.connect() as db:
            count = db.execute(
                f"UPDATE {args.table} SET status='pending',due=0,attempts=0 WHERE source=? AND {key}=? AND status='failed'",
                (args.source, args.id),
            ).rowcount
        print(f"Requeued {count} failed items")


if __name__ == "__main__":
    main()
