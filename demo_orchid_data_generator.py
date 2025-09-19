import os
import json
import requests
from PIL import Image
import time

# Configuration
PHOTOS_DIR = "photos/"
OUTPUT_DIR = "output/"
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Demo orchid data based on real specimens and our botanical glossary
DEMO_ORCHID_DATA = [
    {
        "genus": "Cattleya",
        "hybrid_name": "Cattleya labiata var. autumnalis",
        "parents": "Species variety",
        "description": "Large labellum with prominent callus, crystalline texture on petals, rich magenta coloration with darker veining. Pseudobulbs are elongated with single terminal leaf.",
        "botanical_features": ["Labellum (Lip)", "Petals", "Pseudobulb", "Base Color", "Markings"],
        "image_placeholder": "cattleya_specimen_1.jpg"
    },
    {
        "genus": "Cattleya",
        "hybrid_name": "Cattleya warscewiczii 'Alba'",
        "parents": "Species form",
        "description": "White form showing excellent substance and form. Dorsal sepal broad and overlapping, lateral sepals reflexed. Inflorescence erect with single large flower.",
        "botanical_features": ["Dorsal Sepal", "Lateral Sepals", "Substance", "Form", "Inflorescence Type"],
        "image_placeholder": "cattleya_specimen_2.jpg"
    },
    {
        "genus": "Sarcochilus",
        "hybrid_name": "Sarcochilus fitzgeraldii",
        "parents": "Species",
        "description": "Small white flowers with red markings, arranged in drooping raceme. Aerial roots prominent with thick velamen. Leaves distichous and succulent.",
        "botanical_features": ["Markings", "Inflorescence Type", "Aerial Root", "Velamen", "Leaf Arrangement"],
        "image_placeholder": "sarcochilus_specimen_1.jpg"
    },
    {
        "genus": "Sarcochilus",
        "hybrid_name": "Sarcochilus Heidi × ceciliae",
        "parents": "S. Heidi × S. ceciliae",
        "description": "Hybrid showing intermediate characteristics. Pink overlay color on white base, spotted pattern on labellum. Multiple flowers per spike.",
        "botanical_features": ["Base Color", "Overlay Color", "Color Overlay Pattern", "Flower Count"],
        "image_placeholder": "sarcochilus_specimen_2.jpg"
    },
    {
        "genus": "Zygopetalum",
        "hybrid_name": "Zygopetalum intermedium",
        "parents": "Species",
        "description": "Fragrant species with distinctive tessellated markings on sepals and petals. Labellum white with purple radiating lines. Strong fragrance present.",
        "botanical_features": ["Fragrance", "Markings", "Labellum (Lip)", "Petals", "Dorsal Sepal"],
        "image_placeholder": "zygopetalum_specimen_1.jpg"
    },
    {
        "genus": "Zygopetalum",
        "hybrid_name": "Zygopetalum Advance Australia",
        "parents": "Z. crinitum × Z. maxillare",
        "description": "Modern hybrid with improved flower count and longevity. Waxy texture throughout, balanced symmetry, excellent presentation on arching inflorescence.",
        "botanical_features": ["Flower Count", "Longevity", "Texture", "Symmetry", "Presentation"],
        "image_placeholder": "zygopetalum_specimen_2.jpg"
    }
]

def create_placeholder_image(filename, genus, size=(400, 300)):
    """Create a simple placeholder image for demonstration"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image with genus-appropriate colors
        colors = {
            "Cattleya": (138, 43, 226),      # Purple
            "Sarcochilus": (255, 182, 193),  # Light Pink  
            "Zygopetalum": (50, 205, 50)     # Green
        }
        
        color = colors.get(genus, (128, 128, 128))
        img = Image.new('RGB', size, color=color)
        draw = ImageDraw.Draw(img)
        
        # Add simple text
        try:
            # Try to use a font
            font = ImageFont.load_default()
        except:
            font = None
            
        text = f"{genus}\nDemo Image"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center the text
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        img.save(os.path.join(PHOTOS_DIR, filename))
        return True
        
    except Exception as e:
        print(f"Error creating placeholder image {filename}: {e}")
        return False

def generate_demo_data():
    """Generate demo orchid data and images"""
    print("🌺 Generating Demo Orchid Data for SVO Integration")
    print("=" * 60)
    
    all_metadata = []
    
    for i, orchid in enumerate(DEMO_ORCHID_DATA):
        print(f"Creating specimen {i+1}: {orchid['hybrid_name']}")
        
        # Create placeholder image
        img_filename = orchid['image_placeholder']
        if create_placeholder_image(img_filename, orchid['genus']):
            print(f"  ✅ Created image: {img_filename}")
        else:
            print(f"  ❌ Failed to create image: {img_filename}")
        
        # Add to metadata with enhanced botanical information
        metadata_entry = {
            "genus": orchid['genus'],
            "hybrid_name": orchid['hybrid_name'],
            "parents": orchid['parents'],
            "description": orchid['description'],
            "image_file": img_filename,
            "botanical_features": orchid['botanical_features'],
            "scrape_method": "demo_generated",
            "ai_derivable_features": len([f for f in orchid['botanical_features']]),
            "source": "Demo data for SVO-Orchid Continuum integration"
        }
        
        all_metadata.append(metadata_entry)
        
        time.sleep(0.1)  # Small delay for visual effect
    
    # Save metadata
    metadata_file = os.path.join(OUTPUT_DIR, "SVO_hybrids_metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Demo data generation completed!")
    print(f"📊 Total specimens: {len(all_metadata)}")
    print(f"📁 Images saved to: {PHOTOS_DIR}")
    print(f"📄 Metadata saved to: {metadata_file}")
    
    # Show botanical features coverage
    all_features = set()
    for orchid in all_metadata:
        all_features.update(orchid['botanical_features'])
    
    print(f"🔬 Botanical features covered: {len(all_features)}")
    print("   Features:", ', '.join(sorted(all_features)))
    
    return all_metadata

if __name__ == "__main__":
    generate_demo_data()