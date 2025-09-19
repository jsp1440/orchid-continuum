# Darwin Core Archive Export Guide

## Overview
This directory contains templates for exporting Orchid Atlas data to Darwin Core Archive (DwC-A) format, making it compatible with GBIF, iNaturalist, and other major biodiversity platforms.

## Files
- `occurrence.txt` - Tab-delimited template with all core Darwin Core fields
- `meta.xml` - Metadata descriptor telling GBIF how to interpret the data
- `mapping_sheet.csv` - Crosswalk between your schema and Darwin Core terms

## Schema Field Mapping

### Direct Mappings (Easy)
| Your Field | Darwin Core Field | Notes |
|------------|-------------------|--------|
| `scientific_name` | `scientificName` | Direct copy |
| `genus` | `genus` | Direct copy |
| `species` | `specificEpithet` | Direct copy |
| `region` | `country` or `locality` | Parse as needed |
| `photographer` | `recordedBy` | Direct copy |
| `created_at` | `eventDate` | Format as ISO 8601 |
| `image_url` | `associatedMedia` | Direct copy |

### Calculated Fields
| Darwin Core Field | Calculation | Example |
|------------------|-------------|---------|
| `occurrenceID` | `"ORCHID_" + id` | ORCHID_12345 |
| `basisOfRecord` | Always "HumanObservation" | HumanObservation |
| `kingdom` | Always "Plantae" | Plantae |
| `family` | Always "Orchidaceae" | Orchidaceae |
| `taxonRank` | "species" or "hybrid" | species |
| `institutionCode` | "FCOS" (Five Cities Orchid Society) | FCOS |

### Complex Mappings
| Your Field | Darwin Core Field | Processing |
|------------|-------------------|------------|
| `pod_parent + pollen_parent` | `taxonRemarks` | "Hybrid: Parent1 × Parent2" |
| `cultural_notes` | `occurrenceRemarks` | Combine with other notes |
| `ai_description` | `identificationRemarks` | AI-generated content |
| `native_habitat` | `habitat` | Direct copy |
| `growth_habit` | `lifeStage` | "adult" for flowering |

## Export Process

1. **Query your database** for all orchid records
2. **Transform each field** using the mapping table
3. **Generate occurrence.txt** with tab-separated values
4. **Validate** using GBIF data validator
5. **Package** with meta.xml into ZIP file
6. **Upload** to GBIF or other DwC-A compatible platform

## Python Export Example

```python
def export_to_darwin_core():
    records = OrchidRecord.query.all()
    
    with open('occurrence.txt', 'w') as f:
        # Write header
        f.write(DARWIN_CORE_HEADER + '\n')
        
        for record in records:
            row = [
                f"ORCHID_{record.id}",  # occurrenceID
                record.scientific_name,  # scientificName
                record.author or "",     # scientificNameAuthorship
                "species",               # taxonRank
                "Plantae",              # kingdom
                "Tracheophyta",         # phylum
                "Liliopsida",           # class
                "Asparagales",          # order
                "Orchidaceae",          # family
                record.genus,           # genus
                record.species or "",   # specificEpithet
                "",                     # infraspecificEpithet
                "HumanObservation",     # basisOfRecord
                record.created_at.isoformat() if record.created_at else "",  # eventDate
                # ... continue for all fields
            ]
            f.write('\t'.join(row) + '\n')
```

## GBIF Compatibility Notes

- **Coordinates**: Must be decimal degrees (WGS84)
- **Dates**: ISO 8601 format (YYYY-MM-DD)
- **Required fields**: occurrenceID, scientificName, basisOfRecord
- **Encoding**: UTF-8 only
- **File size**: Recommended < 100MB per file

## Half-Earth Project Integration

The Half-Earth Project can consume DwC-A files directly. Ensure:
- Geographic coordinates are precise
- `establishmentMeans` indicates native vs cultivated
- `conservationStatus` included in `dynamicProperties` JSON

## Validation

Before publishing:
1. Use GBIF Data Validator: https://www.gbif.org/tools/data-validator
2. Check for required fields
3. Validate coordinate precision
4. Ensure taxonomic names match accepted standards

## Publishing Workflow

1. **Monthly exports** from your production database
2. **Automated validation** pipeline
3. **Direct GBIF publishing** via API
4. **Cross-platform syndication** to iNat, EOL, etc.

## Support

For questions about Darwin Core mapping or GBIF publishing, consult:
- GBIF Data Publishing Guidelines
- Darwin Core Quick Reference Guide
- IPT (Integrated Publishing Toolkit) Documentation