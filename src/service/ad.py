from dataclasses import dataclass
from html import escape
from urllib.parse import urlparse
import math


@dataclass
class Ad:
    town: str
    photos: list[str]
    cost: float
    landlord: str
    latitude: float | None
    longitude: float | None
    rooms_amount: str
    link: str
    source: str
    subway_name: str | None
    subway_dist: int | None
    author_name: str

    def __post_init__(self):
        self.cost = float(self.cost)
        if not math.isfinite(self.cost) or self.cost < 0:
            raise ValueError("Invalid price")
        if not self.town or not self.rooms_amount:
            raise ValueError("Missing town or rooms")
        if urlparse(self.link).scheme != "https" or urlparse(
            self.link
        ).hostname not in ("r.onliner.by", "re.kufar.by", "www.kufar.by", "kufar.by"):
            raise ValueError("Invalid advertisement URL")
        self.photos = [
            p for p in self.photos if isinstance(p, str) and p.startswith("https://")
        ][:10]
        if self.latitude is not None and self.longitude is not None:
            self.latitude, self.longitude = float(self.latitude), float(self.longitude)
            if not (-90 <= self.latitude <= 90 and -180 <= self.longitude <= 180):
                raise ValueError("Invalid coordinates")
        else:
            self.latitude = self.longitude = None

    def create_telegram_caption(self):
        def safe(value, limit=120):
            return escape(str(value if value is not None else "Не указано")[:limit])

        text = (
            f"<b>Комнат:</b> {safe(self.rooms_amount)}\n"
            f"<b>Город:</b> {safe(self.town)}\n"
            f"<b>Цена:</b> {self.cost:g} USD\n"
            f"<b>Сдаёт:</b> {safe(self.landlord)}\n"
        )
        if (
            self.subway_name is not None
            and self.subway_dist is not None
            and self.town == "Минск"
        ):
            text += f"🚇 {safe(self.subway_name)}, {self.subway_dist} м\n"
        return text + (
            f"<b>Источник:</b> {safe(self.source)}\n"
            f'<a href="{escape(self.link, quote=True)}">Ссылка</a>\n'
            f"<b>Автор:</b> {safe(self.author_name)}"
        )
