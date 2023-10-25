from geopy.distance import geodesic as GD
import math


class Station:
    def __init__(self, name: str, latitude: float, longitude: float) -> None:
        self.name = name
        self.lat = latitude
        self.lon = longitude

    def distance_to(self, latitude: float, longitude: float) -> int:
        return int(GD((self.lat, self.lon), (latitude, longitude)).m)


subways = [Station('Малиновка', 53.849483, 27.474572),  # 0
           Station('Петровщина', 53.864585, 27.485964),
           Station('Михайлово', 53.876697, 27.496867),
           Station('Грушевка', 53.886704, 27.514799),
           Station('Институт культуры', 53.885709, 27.539715),
           Station('Площадь Ленина', 53.891927, 27.548461),
           Station('Октябрьская', 53.902227, 27.562134),
           Station('Площадь победы', 53.909070, 27.575637),
           Station('Площадь Якуба Колоса', 53.915814, 27.583491),
           Station('Академия наук', 53.921967, 27.599477),
           Station('Парк Челюскинцев', 53.921967, 27.599477),
           Station('Московская', 53.927995, 27.627714),
           Station('Восток', 53.934608, 27.651595),
           Station('Борисовский тракт', 53.938502, 27.665798),
           Station('Уручье', 53.945433, 27.688063),
           Station('Каменная горка', 53.906881, 27.436902),  # 15
           Station('Кунцевщина', 53.906314, 27.454421),
           Station('Спортивная', 53.908519, 27.480847),
           Station('Пушкинская', 53.909635, 27.496597),
           Station('Молодёжная', 53.906414, 27.523808),
           Station('Фрунзенская', 53.905281, 27.540184),
           Station('Немига', 53.905833, 27.553821),
           Station('Купаловская', 53.900455, 27.562066),
           Station('Первомайская', 53.893827, 27.570331),
           Station('Пролетарская', 53.889932, 27.585761),
           Station('Тракторный завод', 53.889322, 27.614876),
           Station('Партизанская', 53.875574, 27.628802),
           Station('Автозаводская', 53.869100, 27.648424),
           Station('Могилёвская', 53.861990, 27.674500),
           Station('Площадь Франтишка Богушевича', 53.896467, 27.538317),  # 29
           Station('Ковальская слобода', 53.877690, 27.549695),
           Station('Вокзальная', 53.889481, 27.547428),
           Station('Юбилейная', 53.905270, 27.541559),  # 32
           ]


def get_closest_subway(latitude: float, longitude: float) -> Station:
    if latitude is None or longitude is None:
        return None
    result = None
    min_dist = math.inf
    for station in subways:
        distance = station.distance_to(latitude, longitude)
        if distance < min_dist:
            min_dist = distance
            result = station
    return result
