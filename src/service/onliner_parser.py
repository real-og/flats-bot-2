import re
from src.service.ad import Ad
from src.shared.towns import normalize_town
from src.shared.subway_map import get_closest_subway

onliner_url = "https://r.onliner.by/sdapi/ak.api/search/apartments"
onliner_params = {"order": "created_at:desc", "page": "1"}


def address_town(address):
    parts = [p.strip() for p in address.split(",")]
    if parts and parts[0] in ("Беларусь", "Республика Беларусь"):
        parts.pop(0)
    # Skip explicitly labelled region/district, do not guess by nearest city.
    parts = [
        p
        for p in parts
        if not re.search(r"область|район|обл\.|р-н|сельский (?:совет|Совет)", p, re.I)
    ]
    if not parts:
        raise ValueError("No settlement in Onliner address")
    town = re.sub(
        r"^(?:(?:г|д|аг|пос)\.\s*|(?:город|деревня|агрогородок)\s+)",
        "",
        parts[0],
        flags=re.I,
    )
    if (
        not town
        or any(c.isdigit() for c in town)
        or re.search(r"ул\.|улица|проспект", town, re.I)
    ):
        raise ValueError("Unrecognized Onliner address")
    return normalize_town(town)


def generate_ad_from_onliner(raw):
    location = raw.get("location") or {}
    lat, lon = location.get("latitude"), location.get("longitude")
    if lat is not None and lon is not None:
        lat, lon = float(lat), float(lon)
    town = address_town(location.get("address") or location.get("user_address") or "")
    subway = get_closest_subway(lat, lon) if town == "Минск" else None
    price = raw.get("price") or {}
    cost = price.get("converted", {}).get("USD", {}).get("amount")
    if cost is None and price.get("currency") == "USD":
        cost = price.get("amount")
    owner = (raw.get("contact") or {}).get("owner")
    rent = raw.get("rent_type") or ""
    rooms = "Комната" if rent == "room" else rent.split("_")[0]
    if rooms != "Комната" and not rooms.isdigit():
        raise ValueError("Invalid rent type")
    return Ad(
        town,
        [raw["photo"]] if raw.get("photo") else [],
        cost,
        "Собственник"
        if owner is True
        else "Агентство"
        if owner is False
        else "Не указано",
        lat,
        lon,
        rooms,
        raw.get("url"),
        "onliner",
        subway.name if subway else None,
        subway.distance_to(lat, lon) if subway else None,
        "Не указано",
    )
