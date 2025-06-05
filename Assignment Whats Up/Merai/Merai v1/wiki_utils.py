# Wikipedia API helpers
import requests
import html

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
