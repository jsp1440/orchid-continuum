import requests
from bs4 import BeautifulSoup
import os
import json

BASE_URL = "https://www.svo.org/index.php?dir=hybrids&genus={}"
GENERAE = ["Sarcochilus", "Zygopetalum", "Cattleya"]
PHOTOS_DIR = "photos/"
os.makedirs(PHOTOS_DIR, exist_ok=True)

all_metadata = []

for genus in GENERAE:
    url = BASE_URL.format(genus)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Example: locate hybrid entries (simplified)
    hybrids = soup.find_all("div", class_="hybrid-entry")[:10]  # first 10 for Sarco and Cattleya
    for h in hybrids:
        name = h.find("h3").text.strip()
        desc = h.find("p", class_="description").text.strip()
        parents = h.find("p", class_="parents").text.strip()
        img_url = h.find("img")["src"]
        
        # Download image
        img_data = requests.get(img_url).content
        img_filename = f"{genus}_{name.replace(' ', '_')}.jpg"
        with open(os.path.join(PHOTOS_DIR, img_filename), "wb") as f:
            f.write(img_data)
        
        all_metadata.append({
            "genus": genus,
            "hybrid_name": name,
            "parents": parents,
            "description": desc,
            "image_file": img_filename
        })

# Save metadata
with open("output/SVO_hybrids_metadata.json", "w", encoding="utf-8") as f:
    json.dump(all_metadata, f, indent=2, ensure_ascii=False)