from functools import lru_cache
from datetime import timedelta
from typing import List
from typing import Tuple
from urllib.parse import quote
from enum import Enum

import requests


class RoutingProfile(Enum):
    TRAFFIC = 'driving-traffic'
    DRIVING = 'driving'
    WALKING = 'walking'
    CYCLING = 'cycling'


def direction_duration(locations: List[Tuple[float, float]],
                       routing_profile: RoutingProfile,
                       token: str) -> timedelta:
    """

    Args:
        locations: a list of coordinates (longitude and latitude) that compose the trip
        routing_profile: specify if the user is driving, walking or cycling
        token: the mapbox token to use

    Returns:

    """
    if 0 > len(locations) > 2:
        raise ValueError('This method calculates the travel time between two locations. However, the input does not '
                         'include the required locations')

    # TODO
    #for location in range(len(locations)):
    #    coordinates_concat = ','.join([str(coordinate) for coordinate in locations[location]])
    quoted_coordinates = quote(f'{locations[0][0]},{locations[0][1]};{locations[1][0]},{locations[1][1]}')

    url = f"https://api.mapbox.com/directions/v5/mapbox/{routing_profile.value}/{quoted_coordinates}"
    querystring = {"alternatives": "false", "geometries": "geojson", "overview": "full", "steps": "false",
                   "notifications": "none",
                   "access_token": token}
    payload = ""
    headers = {"User-Agent": "punctual/1.0.0"}

    try:
        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
        #response.json()['routes'][0]['distance'] / 1000 => distance in km
        return timedelta(minutes=round(response.json()['routes'][0]['duration']) / 60)
    # TODO remove this bare 'except', we can handle exception way better
    except:
        return timedelta(minutes=0)


@lru_cache
def geocode(location: str,
            token: str) -> Tuple[str, Tuple[float, float]]:
    """

    Args:
        location: a string representing an address or a location, such as "Piazza della Repubblica, Rome, Italy"
        token: the mapbox token to use

    Returns:
        a tuple where:
            first item is the full address name matched by mapbox
            second item is a tuple of coordinates (longitude and latitude)
    """
    url = \
        f'https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(location)}.json'
    querystring = {"access_token": token}
    payload = ""
    headers = {"User-Agent": "punctual/1.0.0"}
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    return (response.json()['features'][0]['place_name'],  # full address
            (response.json()['features'][0]['center'][0],  # longitude
            response.json()['features'][0]['center'][1]))  # latitude
