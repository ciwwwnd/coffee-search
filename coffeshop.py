import json
import requests
import os
from geopy import distance
import folium
from flask import Flask


APIKEY = os.environ.get("APIKEY")
number_of_nearest_coffeeshop_around = 5


def get_coffeeshops(file_path):
    with open('coffee.json', 'r', encoding='CP1251') as file:
        file_contents = file.read()
        coffeshops = json.loads(file_contents)
        return coffeshops


def get_coffeeshops_coords(file_path, current_location):
    coffeshops_from_file = get_coffeeshops(file_path)
    coffeeshops = []

    for coffeeshop in coffeshops_from_file:
        coffeeshop_longitude, coffeeshop_latitude = coffeeshop['geoData']['coordinates']

        coffeeshop = {
            'title': coffeeshop['Name'],
            'latitude': coffeeshop_latitude,
            'longitude': coffeeshop_longitude,
            'distance': distance.distance(
                (current_location['latitude'],
                 current_location['longitude']),
                (coffeeshop_latitude, coffeeshop_longitude)).km
        }

        coffeeshops.append(coffeeshop)

    return coffeeshops


def add_placement_mark(current_location, coffeeshops):
  
    coffeeshops_map = folium.Map(
        location=[current_location['latitude'], current_location['longitude']],
        zoom_start=16,
    )

    folium.Marker(
        location=[current_location['latitude'], current_location['longitude']],
        icon=folium.Icon(color="red")
        ).add_to(coffeeshops_map)

    for coffeeshop in coffeeshops:
      folium.Marker(
        location=[coffeeshop['latitude'], coffeeshop['longitude']]
        ).add_to(coffeeshops_map)

    return coffeeshops_map


def read_index():
    with open('index.html') as file:
        return file.read()


def fetch_coordinates(api_key, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": api_key, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def main():
    current_location_name = input("Где вы находитесь? ")
    location_coordinates = fetch_coordinates(APIKEY, current_location_name)
    current_location = {
        'latitude': location_coordinates[1],
        'longitude': location_coordinates[0]
    }

    coffeeshops = get_coffeeshops_coords('coffee_json', current_location)

    limited_coffeeshops = sorted(
      coffeeshops,
      key=lambda x: x['distance']
    )[:number_of_nearest_coffeeshop_around]

    add_placement_mark(current_location, limited_coffeeshops).save('index.html')

    app = Flask(__name__)
    app.add_url_rule('/', 'index', read_index)
    app.run('0.0.0.0')


if __name__ == "__main__":
    main()
