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

#GETTING LOCATION
#Using geocoder to get the location of the user based on their IP address
#This is a simple way to get the location without needing user input
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

#GETTING ZENITH RA/DEC
#RA/DEC is the celestial coordinate system equivalent to latitude and longitude on Earth
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

#GETTING SKYVIEW IMAGE
#SkyView is a web service that provides access to astronomical images from various surveys
#This function retrieves an image from the SkyView service based on the RA/Dec coordinates
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

#GETTING APOD IMAGE
#APOD (Astronomy Picture of the Day) is a popular astronomy website that features a new image or video every day.
def get_apod_image(folder):
    api_key ='aMpwwJNk1KNmIl9BNifQPFVXMhFC8wvT50M7HngJ'
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

#GETTING SENTINEL IMAGE
#Sentinel Hub is a cloud-based platform for processing satellite data
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

        # GETTING HUBBLE IMAGE
        # Hubble Legacy Archive provides access to Hubble Space Telescope images
        def get_hubble_image(ra, dec, folder):
            try:
                # Hubble Legacy Archive cutout service (simple JPEG preview)
                url = "https://hla.stsci.edu/cgi-bin/fitscut.cgi"
                params = {
                    "RA": ra,
                    "DEC": dec,
                    "size": 60,  # arcsec
                    "format": "jpg",
                    "red": "wfpc2_f606w",
                    "output_size": 512
                }
                r = requests.get(url, params=params, timeout=30)
                if r.ok and r.headers.get('Content-Type', '').startswith('image'):
                    filename = os.path.join(folder, "hubble_zenith.jpg")
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    print(f"Hubble image saved as {filename}")
                else:
                    print("Hubble image not available for this position.")
            except Exception as e:
                print(f"Error retrieving Hubble image: {e}")

        # GETTING SDSS IMAGE
        # Sloan Digital Sky Survey provides optical images of the sky
        def get_sdss_image(ra, dec, folder):
            try:
                url = "http://skyserver.sdss.org/dr16/SkyServerWS/ImgCutout/getjpeg"
                params = {
                    "ra": ra,
                    "dec": dec,
                    "scale": 0.4,
                    "width": 512,
                    "height": 512
                }
                r = requests.get(url, params=params, timeout=30)
                if r.ok and r.headers.get('Content-Type', '').startswith('image'):
                    filename = os.path.join(folder, "sdss_zenith.jpg")
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    print(f"SDSS image saved as {filename}")
                else:
                    print("SDSS image not available for this position.")
            except Exception as e:
                print(f"Error retrieving SDSS image: {e}")

        # GETTING PAN-STARRS IMAGE
        # Pan-STARRS provides wide-field images of the sky
        def get_pan_starrs_image(ra, dec, folder):
            try:
                url = "https://ps1images.stsci.edu/cgi-bin/ps1cutouts"
                params = {
                    "pos": f"{ra} {dec}",
                    "filter": "g",
                    "filetypes": "stack",
                    "auxiliary": "no",
                    "size": 512,
                    "output_size": 512,
                    "format": "jpeg"
                }
                r = requests.get(url, params=params, timeout=30)
                if r.ok and r.headers.get('Content-Type', '').startswith('image'):
                    filename = os.path.join(folder, "panstarrs_zenith.jpg")
                    with open(filename, 'wb') as f:
                        f.write(r.content)
                    print(f"Pan-STARRS image saved as {filename}")
                else:
                    print("Pan-STARRS image not available for this position.")
            except Exception as e:
                print(f"Error retrieving Pan-STARRS image: {e}")




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
 