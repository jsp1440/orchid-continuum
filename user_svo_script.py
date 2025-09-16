import subprocess
import sys
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from collections import Counter
import matplotlib.pyplot as plt
import csv
import logging

# --------------------------------------------------------
# Step 1: Automatic Package Installation
# --------------------------------------------------------
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import aiohttp
except ImportError:
    install_package("aiohttp")
    import aiohttp

try:
    from bs4 import BeautifulSoup
except ImportError:
    install_package("beautifulsoup4")
    from bs4 import BeautifulSoup

try:
    import matplotlib.pyplot as plt
except ImportError:
    install_package("matplotlib")
    import matplotlib.pyplot as plt

# --------------------------------------------------------
# Step 2: Configuration
# --------------------------------------------------------
URL = "https://sunsetvalleyorchids.com/htm/archive.html"
OUTPUT_DIR = "output"
CSV_FILENAME = "svo_results.csv"
MAX_RETRIES = 3
TIMEOUT = 10

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --------------------------------------------------------
# Step 3: Scraper / Fetcher
# --------------------------------------------------------
async def fetch(session, url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, timeout=TIMEOUT) as response:
                response.raise_for_status()
                text = await response.text()
                logging.info(f"Fetched {url}")
                return text
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt == MAX_RETRIES:
                logging.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
                return None

async def fetch_all(url):
    async with aiohttp.ClientSession() as session:
        return await fetch(session, url)

# --------------------------------------------------------
# Step 4: Parser
# --------------------------------------------------------
def parse_svo(raw_html):
    svo_list = []
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        # Assuming SVO data is within <p> tags; adjust as necessary
        paragraphs = soup.find_all("p")
        for para in paragraphs:
            text = para.get_text()
            # Basic SVO extraction; refine regex as needed
            matches = re.findall(r"(\w+)\s+(\w+)\s+(\w+)", text)
            svo_list.extend(matches)
        logging.info(f"Parsed {len(svo_list)} SVO tuples")
    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
    return svo_list

# --------------------------------------------------------
# Step 5: Clean Text
# --------------------------------------------------------
def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text.strip()

# --------------------------------------------------------
# Step 6: Clean SVO
# --------------------------------------------------------
def clean_svo(svo_list):
    cleaned = []
    for subj, verb, obj in svo_list:
        cleaned.append((
            clean_text(subj).lower(),
            clean_text(verb).lower(),
            clean_text(obj).lower()
        ))
    return cleaned

# --------------------------------------------------------
# Step 7: Analyze SVO
# --------------------------------------------------------
def analyze_svo(cleaned_svo):
    subjects = [s for s, v, o in cleaned_svo]
    verbs = [v for s, v, o in cleaned_svo]
    objects = [o for s, v, o in cleaned_svo]

    analysis = {
        "subject_freq": Counter(subjects),
        "verb_freq": Counter(verbs),
        "object_freq": Counter(objects),
        "total_svo": len(cleaned_svo)
    }
    return analysis

# --------------------------------------------------------
# Step 8: Visualize SVO
# --------------------------------------------------------
def visualize_svo(analysis):
    # Set matplotlib to use non-interactive backend
    plt.switch_backend('Agg')
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for key in ["subject_freq", "verb_freq", "object_freq"]:
        counter = analysis[key]
        top_items = counter.most_common(10)
        if not top_items:
            continue
        labels, counts = zip(*top_items)
        plt.figure(figsize=(10,5))
        plt.bar(labels, counts, color='skyblue')
        plt.title(f"Top 10 {key}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart to file instead of showing
        chart_path = os.path.join(OUTPUT_DIR, f"{key}_chart.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Chart saved to {chart_path}")

# --------------------------------------------------------
# Step 9: Save Results
# --------------------------------------------------------
def save_results(cleaned_svo, analysis):
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUT_DIR, CSV_FILENAME)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Subject", "Verb", "Object"])
            writer.writerows(cleaned_svo)
        logging.info(f"SVO data saved to {csv_path}")

        summary_path = os.path.join(OUTPUT_DIR, "analysis_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            for key, counter in analysis.items():
                if isinstance(counter, Counter):
                    f.write(f"{key}:\n{counter}\n\n")
                else:
                    f.write(f"{key}: {counter}\n\n")
        logging.info(f"Analysis summary saved to {summary_path}")
    except Exception as e:
        logging.error(f"Error saving results: {e}")

# --------------------------------------------------------
# Step 10: Main Workflow
# --------------------------------------------------------
def main():
    raw_data = asyncio.run(fetch_all(URL))
    if not raw_data:
        print("No data fetched. Exiting.")
        return
    svo_data = parse_svo(raw_data)
    if not svo_data:
        print("No SVO tuples extracted. Exiting.")
        return
    cleaned_svo = clean_svo(svo_data)
    analysis_results = analyze_svo(cleaned_svo)
    visualize_svo(analysis_results)
    save_results(cleaned_svo, analysis_results)
    print("SVO Scraper + Analyzer finished successfully.")

if __name__ == "__main__":
    main()