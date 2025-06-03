from geopy.distance import geodesic
from typing import List, Tuple
import math

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    point1 = (lat1, lng1)
    point2 = (lat2, lng2)
    return geodesic(point1, point2).kilometers

def sort_salespeople_by_distance(
    salespeople: List, 
    target_lat: float, 
    target_lng: float
) -> List[Tuple[any, float]]:
    """
    Sort salespeople by distance from target location
    Returns list of tuples (salesperson, distance_km)
    """
    salesperson_distances = []
    
    for salesperson in salespeople:
        if salesperson.current_latitude and salesperson.current_longitude:
            distance = calculate_distance(
                target_lat, target_lng,
                salesperson.current_latitude, salesperson.current_longitude
            )
            salesperson_distances.append((salesperson, distance))
    
    # Sort by distance
    salesperson_distances.sort(key=lambda x: x[1])
    return salesperson_distances

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Alternative Haversine implementation
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c
