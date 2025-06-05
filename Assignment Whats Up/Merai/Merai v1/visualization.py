# Visualization and image display functions
from PIL import Image
from io import BytesIO
import requests
import matplotlib.pyplot as plt

def display_image(image_url, title, wiki_name=None, get_object_description=None):
    if wiki_name is None:
        wiki_name = title
    desc = get_object_description(wiki_name) if get_object_description else None
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
