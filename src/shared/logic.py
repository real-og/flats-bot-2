from src.service.ad import Ad
from geopy.distance import geodesic as GD 


def is_float(num: str) -> bool:
    """Check whether the string num can be converted to float"""

    if num.isdigit():
       return True
    else:
        try:
            float(num)
            return True
        except ValueError:
            return False

def is_coordinates(input: str) -> bool:
    """Check whether the input is 2 comma-separated coordinates"""

    if len(input.split(',')) != 2:
        return False
    lat, lon = input.split(',')
    if not (is_float(lat.strip()) and (0 <= float(lat.strip()) <= 90)):
        return False
    if not (is_float(lon.strip()) and (0 <= float(lon.strip()) <= 180)):
        return False
    return True


def is_comparable(params: dict, ad: Ad):
        if ad.town != params['town']:
            return False
        if float(ad.cost) > float(params['max_cost']) or float(ad.cost) < float(params['min_cost']):
            return False
        if params['landlord'] != 'Не важно' and params['landlord'] != ad.owner:
            return False
        formated_rooms = 'Комната' if ad.rooms_amount == 0 else str(ad.rooms)
        if formated_rooms not in params['rooms']:
            return False
        if params['isSubwayNeed'] and int(params['subway_dist']) < ad.subway_dist:
            return False
        if params['isPointNeed'] and int(GD((ad.latitude, ad.longitude), (params['lat'], params['lon'])).m) > params['point_dist']:
            return False
        return True