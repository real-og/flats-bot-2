"""Small report over the durable queue; no pandas dependency."""

import json
from collections import defaultdict
from datetime import datetime
from statistics import median
from src.service.store import Store


def analyze_minsk_advertisements(csv_file=None):
    prices = defaultdict(list)
    with Store().connect() as db:
        rows = db.execute(
            "SELECT min(created) AS created,payload FROM outbox GROUP BY source,ad_id"
        )
        for row in rows:
            ad = json.loads(row["payload"])
            if (
                ad["town"] == "Минск"
                and str(ad["rooms_amount"]) == "1"
                and ad["cost"] <= 2000
            ):
                prices[datetime.fromtimestamp(row["created"]).date()].append(ad["cost"])
    lines = [
        "Минск, 1 комната, до $2000. Только объявления, попавшие в очередь доставки."
    ]
    for day, values in sorted(prices.items())[-30:]:
        lines.append(f"{day}: {len(values)} объявл., медиана ${median(values):.0f}")
    return "\n".join(lines) if prices else "Пока нет данных для статистики."
