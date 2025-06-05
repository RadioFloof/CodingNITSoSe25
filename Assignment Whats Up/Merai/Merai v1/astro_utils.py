# Astronomy-related utilities
from skyfield.api import load, Topos, Star, utc
from skyfield.data import hipparcos
import re

def get_visible_objects(lat, lon, user_dt=None, get_object_description=None):
    ts = load.timescale()
    if user_dt:
        t = ts.from_datetime(user_dt)
    else:
        t = ts.now()
    planets = load('de421.bsp')
    earth = planets['earth']
    observer = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    visible = []
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
    with load.open(hipparcos.URL) as f:
        stars = hipparcos.load_dataframe(f)
    bright_stars = stars[stars['magnitude'] < 2.0]
    for hip, star_row in bright_stars.iterrows():
        star = Star(ra_hours=star_row['ra_hours'], dec_degrees=star_row['dec_degrees'])
        astrometric = observer.at(t).observe(star)
        alt, az, _ = astrometric.apparent().altaz()
        if alt.degrees > 0:
            star_name = star_row.get('proper')
            if isinstance(star_name, str) and star_name.strip():
                common_name = star_name.strip()
            else:
                desc = get_object_description(f"HIP {hip}") if get_object_description else None
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
    seen = set()
    unique_visible = []
    for obj in sorted(visible, key=lambda x: -x['altitude']):
        key = (obj['name'], obj['type'])
        if key not in seen:
            seen.add(key)
            unique_visible.append(obj)
    return unique_visible
