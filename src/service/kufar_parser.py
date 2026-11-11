from decimal import Decimal
from src.service.ad import Ad
from src.shared.towns import normalize_town
from src.shared.subway_map import get_closest_subway

kufar_url = "https://api.kufar.by/search-api/v2/search/rendered-paginated"
kufar_params = {
    "cat": "1010",
    "cur": "BYR",
    "gtsy": "country-belarus",
    "lang": "ru",
    "size": "100",
    "typ": "let",
    "sort": "lst.d",
}


def generate_ad_from_kufar(raw, room=False):
    params = {
        p["p"]: p
        for p in raw.get("ad_parameters", [])
        if isinstance(p, dict) and "p" in p
    }
    town = next(
        (
            params[p].get("vl")
            for p in ("region", "region2")
            if params.get(p, {}).get("vl") == "Минск"
        ),
        None,
    )
    town = town or params.get("area", {}).get("vl")
    town = normalize_town(town)
    coords = params.get("coordinates", {}).get("v")
    lon, lat = coords if isinstance(coords, list) and len(coords) == 2 else (None, None)
    if lat is not None:
        lat, lon = float(lat), float(lon)
    subway = get_closest_subway(lat, lon) if town == "Минск" else None
    price = raw.get("price_usd")
    if price is None:
        price = next(
            (
                p["price"]
                for p in raw.get("calculator", [])
                if p.get("currency") == "USD"
            ),
            None,
        )
    if price is None:
        raise ValueError("Missing USD price")
    # Kufar represents monetary values as integer minor units.
    cost = float(Decimal(str(price)) / 100)
    author = next(
        (
            p.get("v")
            for p in raw.get("account_parameters", [])
            if p.get("p") in ("name", "contact_person")
        ),
        "Не указано",
    )
    owner = raw.get("company_ad")
    return Ad(
        town,
        [
            f"https://rms4.kufar.by/v1/gallery/{i['path']}"
            for i in raw.get("images", [])
            if i.get("path")
        ],
        cost,
        "Агентство"
        if owner is True
        else "Собственник"
        if owner is False
        else "Не указано",
        lat,
        lon,
        "Комната" if room else str(params.get("rooms", {}).get("v") or ""),
        raw.get("ad_link"),
        "kufar",
        subway.name if subway else None,
        subway.distance_to(lat, lon) if subway else None,
        author,
    )
