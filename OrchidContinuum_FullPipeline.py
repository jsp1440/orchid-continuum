# OrchidContinuum_FullPipeline.py
# Fully integrated Orchid Continuum pipeline with all options

import os
import pandas as pd
import json
from pathlib import Path

# ----------------------------
# CONFIGURATION
# ----------------------------
GLOSSARY_CSV = "data/Orchid_Floral_Glossary_Master.csv"
GLOSSARY_JSON = "data/Orchid_Floral_Glossary_Master.json"
PHOTO_DIR = "photos/"
OUTPUT_CSV = "output/Orchid_Inferred_Traits.csv"
OUTPUT_JSON = "output/Orchid_Inferred_Traits.json"

SCHEMA_LAYERS = [
    "Taxonomic Layer",
    "Morphological Layer",
    "Phenotypic Trait",
    "Quantitative Trait",
    "Judging Trait",
    "Environmental",
    "Provenance & Media Layer"
]

# ----------------------------
# STEP 1: LOAD GLOSSARY
# ----------------------------
def load_glossary(csv_path=None, json_path=None):
    if csv_path:
        df = pd.read_csv(csv_path)
        return df
    elif json_path:
        with open(json_path, "r") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    else:
        raise ValueError("Provide either CSV or JSON path")

# ----------------------------
# STEP 2: MAP TERMS TO SCHEMA
# ----------------------------
def map_terms_to_schema(glossary_df, schema_layers):
    layer_mapping = {layer: [] for layer in schema_layers}
    for _, row in glossary_df.iterrows():
        layer = row['Category']
        if layer in layer_mapping:
            layer_mapping[layer].append(row.to_dict())
    return layer_mapping

# ----------------------------
# STEP 3: AI TRAIT INFERENCE (STUB)
# Replace with actual AI model
# ----------------------------
def infer_traits_from_photo(photo_path, glossary_layer_terms):
    inferred = {}
    for term in glossary_layer_terms:
        if term['AI_Derivable']:
            # Placeholder for AI inference
            inferred[term['Term']] = f"AI_value_for_{term['Term']}"
    return inferred

# ----------------------------
# STEP 4: PROCESS ALL PHOTOS
# ----------------------------
def process_all_photos(photo_dir, layer_terms):
    all_results = []
    photo_dir_path = Path(photo_dir)
    photos = [p for p in photo_dir_path.glob("*") if p.suffix.lower() in [".jpg",".jpeg",".png"]]
    for photo in photos:
        photo_result = {"photo_file": str(photo)}
        for layer, terms in layer_terms.items():
            traits = infer_traits_from_photo(photo, terms)
            photo_result.update(traits)
        all_results.append(photo_result)
    return all_results

# ----------------------------
# STEP 5: SAVE RESULTS
# ----------------------------
def save_results(all_results, csv_path, json_path):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame(all_results)
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")

# ----------------------------
# MAIN PIPELINE
# ----------------------------
def main():
    print("Loading glossary...")
    df_glossary = load_glossary(csv_path=GLOSSARY_CSV)
    
    print("Mapping glossary to schema layers...")
    layer_terms = map_terms_to_schema(df_glossary, SCHEMA_LAYERS)
    
    print(f"Processing photos in {PHOTO_DIR} ...")
    all_results = process_all_photos(PHOTO_DIR, layer_terms)
    
    print("Saving results...")
    save_results(all_results, OUTPUT_CSV, OUTPUT_JSON)
    
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    main()