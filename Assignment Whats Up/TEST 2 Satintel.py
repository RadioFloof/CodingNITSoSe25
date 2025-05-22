import os
import sys
import requests
import geocoder
from datetime import datetime
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
import re
import base64

import astropy.units as u

def get_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            lat, lon = g.latlng
            return lat, lon
        else:
            print("Could not detect location.")
            sys.exit(1)
    except Exception as e:
        print(f"Error detecting location: {e}")
        sys.exit(1)

def get_zenith_ra_dec(lat, lon):
    try:
        location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg)
        now = Time(datetime.utcnow())
        altaz = AltAz(location=location, obstime=now)
        zenith = SkyCoord(alt=90*u.deg, az=0*u.deg, frame=altaz)
        zenith_icrs = zenith.transform_to('icrs')
        return zenith_icrs.ra.deg, zenith_icrs.dec.deg
    except Exception as e:
        print(f"Error calculating zenith RA/Dec: {e}")
        sys.exit(1)

def get_skyview_image(ra, dec, folder):
    url = "https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl"
    params = {
        "Position": f"{ra},{dec}",
        "Survey": "DSS",
        "Return": "FITS",
        "pixels": "600"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.ok:
            # SkyView returns a page with links, not the image directly
            # Find the first .fits or .jpg link
            matches = re.findall(r'href="([^"]+\.(jpg|png|fits))"', r.text)
            if matches:
                img_url = matches[0][0]
                if not img_url.startswith("http"):
                    img_url = "https://skyview.gsfc.nasa.gov" + img_url
                img_data = requests.get(img_url).content
                ext = img_url.split('.')[-1]
                filename = os.path.join(folder, f"skyview_zenith.{ext}")
                with open(filename, 'wb') as f:
                    f.write(img_data)
                print(f"SkyView image saved as {filename}")
            else:
                print("SkyView image link not found.")
        else:
            print("SkyView API request failed.")
    except Exception as e:
        print(f"Error retrieving SkyView image: {e}")

def get_apod_image(folder):
    api_key = os.environ.get('NASA_API_KEY')
    if not api_key:
        print("NASA_API_KEY not set in environment.")
        return
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": api_key}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.ok:
            data = r.json()
            img_url = data.get('hdurl') or data.get('url')
            if img_url and img_url.endswith(('jpg', 'png', 'jpeg')):
                img_data = requests.get(img_url).content
                ext = img_url.split('.')[-1]
                filename = os.path.join(folder, f"apod.{ext}")
                with open(filename, 'wb') as f:
                    f.write(img_data)
                print(f"APOD image saved as {filename}")
            else:
                print("APOD image is not a standard image format.")
        else:
            print("APOD API request failed.")
    except Exception as e:
        print(f"Error retrieving APOD image: {e}")

def get_sentinel_image(lat, lon, folder):
    creds = os.environ.get('SENTINEL_HUB_CREDENTIALS')
    if not creds:
        print("SENTINEL_HUB_CREDENTIALS not set in environment.")
        return
    try:
        # Credentials should be "client_id:client_secret"
        client_id, client_secret = creds.split(':')
        # Get OAuth token
        token_url = "https://services.sentinel-hub.com/oauth/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        token_resp = requests.post(token_url, data=token_data, timeout=30)
        token_resp.raise_for_status()
        access_token = token_resp.json()['access_token']

        # Request image
        bbox = [lon-0.01, lat-0.01, lon+0.01, lat+0.01]  # Small area around point
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox
                },
                "data": [{
                    "type": "sentinel-2-l1c"
                }]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [{"identifier": "default", "format": {"type": "image/png"}}]
            }
        }
        img_url = "https://services.sentinel-hub.com/api/v1/process"
        headers = {"Authorization": f"Bearer {access_token}"}
        img_resp = requests.post(img_url, json=payload, headers=headers, timeout=60)
        if img_resp.ok:
            filename = os.path.join(folder, "sentinel_location.png")
            with open(filename, 'wb') as f:
                f.write(img_resp.content)
            print(f"Sentinel image saved as {filename}")
        else:
            print("Sentinel Hub API request failed.")
    except Exception as e:
        print(f"Error retrieving Sentinel image: {e}")

def main():
    lat, lon = get_location()
    print(f"Detected location: lat={lat}, lon={lon}")
    ra, dec = get_zenith_ra_dec(lat, lon)
    folder = r"D:\NITM ED\Coding - Python\Final Whatsups\satellite_images"
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except Exception as e:
            print(f"Could not create folder: {e}")
            sys.exit(1)
    print(f"Zenith RA: {ra:.4f}, Dec: {dec:.4f}")

    folder = input("Enter folder path to save images: ").strip()
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except Exception as e:
            print(f"Could not create folder: {e}")
            sys.exit(1)

    get_skyview_image(ra, dec, folder)
    get_apod_image(folder)
    get_sentinel_image(lat, lon, folder)

if __name__ == "__main__":
    main()
    
    
    #export 