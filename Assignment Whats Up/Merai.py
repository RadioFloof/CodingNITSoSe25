import geocoder
from skyfield.api import load, Topos
from datetime import datetime
import requests
from io import BytesIO

import matplotlib.pyplot as plt

# Step 1: Get User Location
def get_user_location():
    permission = input("Do you allow access to your location? (yes/no): ").strip().lower()
    if permission != 'yes':
        print("Location access denied. Exiting.")
        exit()
    g = geocoder.ip('me')
    if g.ok:
        lat, lon = g.latlng
        address = g.city + ", " + g.country if g.city and g.country else "Unknown location"
        print(f"Detected location: {address} ({lat}, {lon})")
        return lat, lon, address
    else:
        print("Could not determine location.")
        exit()

# Step 2: Retrieve Astronomical Data
def get_visible_planets(lat, lon):
    ts = load.timescale()
    t = ts.now()
    planets = load('de421.bsp')
    earth = planets['earth']
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    planet_keys = {
        'Mercury': 'mercury',
        'Venus': 'venus',
        'Mars': 'mars',
        'Jupiter': 'jupiter barycenter',
        'Saturn': 'saturn barycenter'
    }
    visible = []
    for name, key in planet_keys.items():
        try:
            planet = planets[key]
            astrometric = observer.at(t).observe(planet)
            alt, az, distance = astrometric.apparent().altaz()
            if alt.degrees > 0:
                visible.append({
                    'name': name,
                    'type': 'Planet',
                    'altitude': round(alt.degrees, 2),
                    'azimuth': round(az.degrees, 2)
                })
        except KeyError:
            continue
    return visible

# Step 3: Retrieve and Display Object Images
def get_object_image_url(name):
    # Use Wikipedia API to get image
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if 'thumbnail' in data and 'source' in data['thumbnail']:
            return data['thumbnail']['source']
    return None

def display_image(image_url, title):
    if not image_url:
        print(f"No image found for {title}.")
        return
    resp = requests.get(image_url)
    if resp.status_code == 200:
        img = plt.imread(BytesIO(resp.content), format='jpg')
        plt.imshow(img)
        plt.axis('off')
        plt.title(title)
        plt.show()
    else:
        print(f"Could not retrieve image for {title}.")

# Main Program
def main():
    lat, lon, address = get_user_location()
    print("\nFetching visible planets from your location...\n")
    visible_objects = get_visible_planets(lat, lon)
    if not visible_objects:
        print("No planets are currently visible from your location.")
        return
    for obj in visible_objects:
        print(f"Name: {obj['name']}")
        print(f"Type: {obj['type']}")
        print(f"Altitude: {obj['altitude']}°")
        print(f"Azimuth: {obj['azimuth']}°")
        image_url = get_object_image_url(obj['name'] + " (planet)")
        display_image(image_url, obj['name'])
        print("-" * 40)

if __name__ == "__main__":
    main()