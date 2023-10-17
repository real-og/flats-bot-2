
from src.shared.subway_map import subways
from geopy.distance import geodesic as GD 
from geopy.geocoders import Nominatim


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


def is_comparable(params: dict, ad):
        if params['town'] != 'Вся Беларусь' and ad.town != params['town']:
            return False
        
        if float(ad.cost) > float(params['maxCost']) or float(ad.cost) < float(params['minCost']):
            return False
        
        if params['landlord'] != 'Не важно' and params['landlord'] != ad.landlord:
            return False
        
        formated_rooms = 'Комната' if ad.rooms_amount == 0 else str(ad.rooms_amount)
        if formated_rooms not in params['rooms']:
            return False
        
        if params['isSubwayNeed']:
            is_comparable_by_subway = False
            for subway_index in params['subways']:
                if subways[int(subway_index)].distance_to(ad.latitude, ad.longitude) <= params['subway_dist']:
                    is_comparable_by_subway = True
                    break
            if not is_comparable_by_subway:
                return False
        
        if params['isPointNeed'] and int(GD((ad.latitude, ad.longitude), (params['lat'], params['lon'])).m) > params['point_dist']:
            return False
        return True

def get_city_by_cords(lat, lon):
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="flats-finding")
    location = geolocator.reverse(f"{lat}, {lon}", language='ru')
    if location.raw.get('address', dict()).get('city'):
        return location.raw.get('address', dict()).get('city')
    else:
        return location.raw.get('address', dict()).get('town')