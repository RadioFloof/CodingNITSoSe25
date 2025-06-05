import geocoder
from skyfield.api import load, Topos
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image
import html
from skyfield.api import utc
import re
import matplotlib.pyplot as plt
from skyfield.data import hipparcos
from skyfield.api import Star

# Step 1: Get User Location (Working well do not touch )
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

# Step 1.1: Get User date time or real time (Working well do not touch )
def get_user_datetime():
    user_input = input("Enter date and time in YYYY-MM-DD HH:MM (24h, local) or press Enter for now: ").strip()
    if not user_input:
        return None  # Use current time
    try:
        dt = datetime.strptime(user_input, "%Y-%m-%d %H:%M")
        dt = dt.replace(tzinfo=utc)  # Make datetime timezone-aware (UTC)
        return dt
    except Exception:
        print("Invalid format. Using current time.")
        return None

# Step 2: Retrieve Astronomical Data
def get_visible_objects(lat, lon, user_dt=None):
    ts = load.timescale()
    if user_dt:
        t = ts.from_datetime(user_dt)
    else:
        t = ts.now()
    planets = load('de421.bsp')
    earth = planets['earth']
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    visible = []
    
    # For Planets, Sun, Moon
    for name in planets.names():
        if name == 'earth':
            continue
        try:
            planet = planets[name]
            alt, az, _ = observer.at(t).observe(planet).apparent().altaz()
            if alt.degrees > 0:
                pretty_name = name.replace(' barycenter', '').capitalize()
                obj_type = 'Planet' if pretty_name in ['Mercury','Venus','Earth','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto'] else pretty_name
                visible.append({
                    'name': pretty_name,
                    'type': obj_type,
                    'altitude': round(alt.degrees, 2),
                    'azimuth': round(az.degrees, 2),
                    'raw_name': name
                })
        except Exception:
            continue
    # for Bright stars (Hipparcos, mag < 2.0)
    with load.open(hipparcos.URL) as f:
        stars = hipparcos.load_dataframe(f)
    bright_stars = stars[stars['magnitude'] < 2.0]
    for hip, star_row in bright_stars.iterrows():
        star = Star(ra_hours=star_row['ra_hours'], dec_degrees=star_row['dec_degrees'])
        astrometric = observer.at(t).observe(star)
        alt, az, _ = astrometric.apparent().altaz()
        if alt.degrees > 0:
            # Try to get a common name from 'proper', else fetch from Wikipedia description, else None
            star_name = star_row.get('proper')
            if isinstance(star_name, str) and star_name.strip():
                common_name = star_name.strip()
            else:
                # Try to get name from Wikipedia description
                desc = get_object_description(f"HIP {hip}")
                if desc:
                    match = re.match(r"([A-Z][a-zA-Z0-9\-]*) ", desc)
                    if match:
                        common_name = match.group(1)
                    else:
                        common_name = None
                else:
                    common_name = None
            if common_name:
                name_to_use = f"Common Name: {common_name} | Name: HIP {hip}"
            else:
                name_to_use = f"Common Name: None | Name: HIP {hip}"
            constellation = star_row['constellation'] if 'constellation' in star_row else ''
            visible.append({
                'name': name_to_use,
                'type': 'Star',
                'altitude': round(alt.degrees, 2),
                'azimuth': round(az.degrees, 2),
                'raw_name': f"HIP {hip}",
                'constellation': constellation
            })
    # Remove duplicates and sort by altitude descending
    seen = set()
    unique_visible = []
    for obj in sorted(visible, key=lambda x: -x['altitude']):
        key = (obj['name'], obj['type'])
        if key not in seen:
            seen.add(key)
            unique_visible.append(obj)
    return unique_visible

# Step 3: Retrieve and Display Object Images
def get_object_image_url(name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if 'thumbnail' in data and 'source' in data['thumbnail']:
                return data['thumbnail']['source']
    except Exception:
        pass
    return None

def display_image(image_url, title, wiki_name=None):
    if wiki_name is None:
        wiki_name = title
    desc = get_object_description(wiki_name)
    print(f"Description for {title}:\n{desc}\n" if desc else f"No description found for {title}.")
    if not image_url:
        print(f"No image found for {title}.")
        return
    try:
        resp = requests.get(image_url, timeout=5)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            plt.imshow(img)
            plt.axis('off')
            plt.title(title)
            plt.show()
        else:
            print(f"Could not retrieve image for {title}.")
    except Exception:
        print(f"Could not retrieve image for {title}.")

# New helper function to get a readable description from Wikipedia API
def get_object_description(name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if 'extract' in data:
                return html.unescape(data['extract'])
    except Exception:
        pass
    return None

# Main Program
def main():
    lat, lon, address = get_user_location()
    user_dt = get_user_datetime()
    print("\nFetching visible astronomical objects from your location...\n")
    visible_objects = get_visible_objects(lat, lon, user_dt)
    if not visible_objects:
        print("No astronomical objects are currently visible from your location.")
        return
    print("Visible astronomical objects from your location are (sorted by altitude):")
    for obj in visible_objects:
        extra = f" in {obj['constellation']}" if obj.get('constellation') else ''
        print(f"- {obj['name']} ({obj['type']}){extra}")
    save = input("\nWould you like to save this list to a file? (yes/no): ").strip().lower()
    if save == 'yes':
        with open('visible_objects.txt', 'w', encoding='utf-8') as f:
            for obj in visible_objects:
                extra = f" in {obj.get('constellation')}" if obj.get('constellation') else ''
                f.write(f"- {obj['name']} ({obj['type']}){extra}\n")
        print("List saved to visible_objects.txt\n")
    input("\nHit enter to learn more about each object...")
    for obj in visible_objects:
        # For stars, extract HIP and common name for display and Wikipedia lookup
        if obj['type'] == 'Star':
            hip_match = re.search(r"HIP (\d+)", obj['name'])
            hip_name = f"HIP {hip_match.group(1)}" if hip_match else obj['name']
            # Try to extract common name from obj['name']
            common_name_match = re.search(r"Common Name: ([^|]+)", obj['name'])
            common_name = common_name_match.group(1).strip() if common_name_match else None
            # If common name is None or 'None', try to extract from Wikipedia description
            if not common_name or common_name == 'None':
                desc = get_object_description(hip_name)
                if desc:
                    match = re.match(r"([A-Z][a-zA-Z0-9\-]*)[ ,]", desc)
                    if match:
                        common_name = match.group(1)
            print(f"Name: {hip_name}")
            print(f"Common Name: {common_name if common_name and common_name != 'None' else 'N/A'}")
            print(f"Type: {obj['type']}")
            if obj.get('constellation'):
                print(f"Constellation: {obj['constellation']}")
            print(f"Altitude: {obj['altitude']}°")
            print(f"Azimuth: {obj['azimuth']}°")
            # Try to get image using common name first, then HIP number
            image_url = None
            wiki_name = None
            if common_name and common_name != 'N/A' and common_name != 'None':
                # Try both 'common_name (star)' and 'common_name' for Wikipedia image
                image_url = get_object_image_url(common_name + " (star)")
                wiki_name = common_name + " (star)"
                if not image_url:
                    image_url = get_object_image_url(common_name + " (astronomy)")
                    wiki_name = common_name + " (astronomy)"
                if not image_url:
                    image_url = get_object_image_url(common_name)
                    wiki_name = common_name
            if not image_url:
                image_url = get_object_image_url(hip_name)
                wiki_name = hip_name
            # If still not found, try the Bayer designation from Wikipedia description
            if not image_url and desc:
                bayer_match = re.search(r"designation ([^,\. ]+)", desc, re.IGNORECASE)
                if bayer_match:
                    bayer_name = bayer_match.group(1)
                    image_url = get_object_image_url(bayer_name)
                    wiki_name = bayer_name
        elif obj['name'] in ['Sun', 'Moon']:
            print(f"Name: {obj['name']}")
            print(f"Type: {obj['type']}")
            print(f"Altitude: {obj['altitude']}°")
            print(f"Azimuth: {obj['azimuth']}°")
            wiki_name = obj['name']
            image_url = get_object_image_url(obj['name'])
        elif obj['type'] == 'Planet':
            print(f"Name: {obj['name']}")
            print(f"Type: {obj['type']}")
            print(f"Altitude: {obj['altitude']}°")
            print(f"Azimuth: {obj['azimuth']}°")
            wiki_name = obj['name'] + " (planet)"
            image_url = get_object_image_url(wiki_name)
        else:
            print(f"Name: {obj['name']}")
            print(f"Type: {obj['type']}")
            print(f"Altitude: {obj['altitude']}°")
            print(f"Azimuth: {obj['azimuth']}°")
            wiki_name = obj['name']
            image_url = get_object_image_url(wiki_name)
        display_image(image_url, wiki_name, wiki_name=wiki_name)
        print("-" * 40)

if __name__ == "__main__":
    main()