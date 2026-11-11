from src.service.kufar_parser import generate_ad_from_kufar as parse_flat


def generate_ad_from_kufar(raw):
    return parse_flat(raw, room=True)
