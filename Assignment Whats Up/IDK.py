import geocoder
from skyfield.api import load, Topos, Horizons
from datetime import datetime, timezone
import wikipedia
import requests
import matplotlib.pyplot as plt

# --- 1. Get User Location ---
def get_user_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            lat, lon = g.latlng
            print(f"Detected location: {lat:.4f}, {lon:.4f}")
            return lat, lon
    except Exception:
        pass
    # Fallback: manual input
    print("Could not detect location automatically.")
    lat = float(input("Enter your latitude (e.g. 28.61): "))
    lon = float(input("Enter your longitude (e.g. 77.23): "))
    return lat, lon

# --- 2. Load Ephemeris ---
planets = load('de421.bsp')
ts = load.timescale()

# --- 3. Define Objects of Interest ---
OBJECTS = {
    'Mercury': (planets['mercury'], 'Planet'),
    'Venus': (planets['venus'], 'Planet'),
    'Mars': (planets['mars'], 'Planet'),
    'Jupiter': (planets['jupiter barycenter'], 'Planet'),
    'Saturn': (planets['saturn barycenter'], 'Planet'),
    'Uranus': (planets['uranus barycenter'], 'Planet'),
    'Neptune': (planets['neptune barycenter'], 'Planet'),
    'Moon': (planets['moon'], 'Moon'),
}

# List of bright asteroids (add more as needed)
ASTEROIDS = [
    {'name': 'Ceres', 'id': '1'},
    {'name': 'Vesta', 'id': '4'},
    {'name': 'Pallas', 'id': '2'},
    {'name': 'Hygiea', 'id': '10'},
]

# --- 4. Compute Altitude/Azimuth ---
def get_visible_objects(lat, lon):
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
    t = ts.now()
    visible = []
    # Planets and Moon
    for name, (obj, obj_type) in OBJECTS.items():
        astrometric = (planets['earth'] + observer).at(t).observe(obj)
        alt, az, _ = astrometric.apparent().altaz()
        if alt.degrees > 0:
            visible.append({'name': name, 'alt': alt.degrees, 'az': az.degrees, 'type': obj_type})
    # Asteroids via JPL Horizons
    for asteroid in ASTEROIDS:
        try:
            eph = Horizons(id=asteroid['id'], location={'latitude': lat, 'longitude': lon}, epochs=t.tt)
            astrometric = eph.observe()
            alt, az, _ = astrometric.apparent().altaz()
            if alt.degrees > 0:
                visible.append({'name': asteroid['name'], 'alt': alt.degrees, 'az': az.degrees, 'type': 'Asteroid'})
        except Exception:
            pass
    return visible

# --- 5. Wikipedia Info ---
def get_wikipedia_info(name):
    try:
        page = wikipedia.page(name)
        summary = wikipedia.summary(name, sentences=2)
        # Get first image
        image_url = page.images[0] if page.images else None
        return summary, image_url
    except Exception:
        return "No summary available.", None

# --- 6. NASA SBDB API (for asteroids, here as placeholder) ---
def get_sbdb_info(name):
    # For planets and moon, skip SBDB
    asteroid_ids = {a['name']: a['id'] for a in ASTEROIDS}
    if name in asteroid_ids:
        try:
            url = f'https://ssd-api.jpl.nasa.gov/sbdb.api?sstr={asteroid_ids[name]}'
            resp = requests.get(url, timeout=5)
            if resp.ok:
                data = resp.json()
                phys = data.get('phys_par', {})
                return phys
        except Exception:
            pass
    return {}

# --- 7. Visual Sky Map ---
def plot_sky_map(visible):
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {'Planet': 'orange', 'Moon': 'gray', 'Asteroid': 'green'}
    markers = {'Planet': 'o', 'Moon': 's', 'Asteroid': '^'}
    for obj in visible:
        alt = obj['alt']
        az = obj['az']
        obj_type = obj['type']
        name = obj['name']
        ax.scatter(az, alt, color=colors.get(obj_type, 'blue'), marker=markers.get(obj_type, 'o'), s=100, label=obj_type if name == visible[0]['name'] else "")
        ax.text(az, alt + 2, name, fontsize=9, ha='center')
    ax.set_xlabel('Azimuth (°)')
    ax.set_ylabel('Altitude (°)')
    ax.set_title('Visible Sky Objects (Above Horizon)')
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 90)
    ax.grid(True)
    # Custom legend
    handles = [plt.Line2D([0], [0], marker=markers[t], color='w', label=t, markerfacecolor=colors[t], markersize=10) for t in colors]
    ax.legend(handles=handles, loc='upper right')
    plt.tight_layout()
    plt.show()

# --- 8. Main ---
def main():
    lat, lon = get_user_location()
    visible = get_visible_objects(lat, lon)
    print("\nObjects currently above the horizon:\n")
    for obj in visible:
        name = obj['name']
        alt = obj['alt']
        az = obj['az']
        obj_type = obj['type']
        print(f"Name: {name}")
        print(f"  Type: {obj_type}")
        print(f"  Altitude: {alt:.2f}°")
        print(f"  Azimuth: {az:.2f}°")
        summary, image_url = get_wikipedia_info(name)
        print(f"  Description: {summary}")
        if image_url:
            print(f"  Image: {image_url}")
        # Physical properties for asteroids
        if obj_type == 'Asteroid':
            phys = get_sbdb_info(name)
            if phys:
                for k, v in phys.items():
                    print(f"  {k}: {v}")
        print("-" * 40)
    if visible:
        plot_sky_map(visible)

if __name__ == "__main__":
    main()