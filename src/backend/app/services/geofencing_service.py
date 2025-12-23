import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate distance between two points in meters.
    """
    R = 6371000  # Radius of Earth in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    meters = R * c
    return meters

def is_inside_geofence(current_lat, current_lon, target_lat, target_lon, radius_meters):
    distance = calculate_distance(current_lat, current_lon, target_lat, target_lon)
    return distance <= radius_meters, distance