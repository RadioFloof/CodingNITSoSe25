# Location and datetime input functions
import geocoder
from datetime import datetime
from skyfield.api import utc

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
