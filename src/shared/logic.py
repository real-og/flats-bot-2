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