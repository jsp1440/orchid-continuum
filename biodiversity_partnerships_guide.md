# Biodiversity Platform Partnerships Guide

## Overview
This guide outlines integration strategies for connecting the Orchid Atlas with major biodiversity platforms, databases, and conservation initiatives. Each partnership enables data sharing, taxonomic validation, and global conservation efforts.

---

## 🌍 World Flora Online (WFO) / Plants of the World Online (POWO)

### Purpose
Taxonomic backbone and nomenclatural authority for all plant species globally.

### Integration Strategy
```python
# Nightly taxonomy reconciliation
def sync_with_wfo():
    wfo_api = "http://www.worldfloraonline.org/api/v1/"
    
    for orchid in OrchidRecord.query.all():
        response = requests.get(f"{wfo_api}search", params={
            'query': orchid.scientific_name,
            'kingdom': 'Plantae',
            'family': 'Orchidaceae'
        })
        
        if response.json()['results']:
            wfo_data = response.json()['results'][0]
            orchid.wfo_id = wfo_data['taxonID']
            orchid.accepted_name = wfo_data['acceptedName']
            orchid.taxonomic_status = wfo_data['taxonomicStatus']
            orchid.author = wfo_data['scientificNameAuthorship']
```

### Data Exchange
- **Send**: Scientific names for validation
- **Receive**: Accepted names, synonymy, authorship, taxonomic status
- **Schedule**: Daily automated sync
- **API Endpoint**: `http://www.worldfloraonline.org/api/v1/`

### Implementation Checklist
- [ ] Register for WFO API access
- [ ] Create taxonomy reconciliation script  
- [ ] Add WFO ID field to database schema
- [ ] Schedule nightly sync job
- [ ] Create conflict resolution workflow

---

## 📊 Global Biodiversity Information Facility (GBIF)

### Purpose
Primary portal for sharing biodiversity occurrence data globally.

### Integration Strategy
```python
# Publish DwC-A to GBIF
def publish_to_gbif():
    # Export using Darwin Core mapping
    export_to_darwin_core()
    
    # Create GBIF dataset
    dataset_metadata = {
        'title': 'Five Cities Orchid Society Collection',
        'description': 'Comprehensive orchid occurrence data',
        'license': 'CC-BY-NC',
        'contact': 'curator@fivecitiescalifornia.org'
    }
    
    # Upload via GBIF IPT or API
    gbif_client.publish_dataset(metadata, dwc_archive_path)
```

### Data Exchange
- **Send**: Occurrence records via DwC-A format
- **Receive**: Global occurrence data for range modeling
- **Schedule**: Monthly data publications
- **Format**: Darwin Core Archive (DwC-A)

### Implementation Checklist
- [ ] Complete DwC-A export system (see `/darwin_core_export/`)
- [ ] Register as GBIF data publisher
- [ ] Set up IPT (Integrated Publishing Toolkit) instance
- [ ] Create automated monthly export pipeline
- [ ] Monitor data quality feedback from GBIF

---

## 🔬 iNaturalist Global Orchid Project

### Purpose
Citizen science platform for orchid observations and identification.

### Integration Strategy
```python
# Cross-pollinate with iNaturalist data
def sync_with_inat():
    inat_api = "https://api.inaturalist.org/v1/"
    
    # Pull orchid observations for taxonomy updates
    response = requests.get(f"{inat_api}observations", params={
        'taxon_id': 47218,  # Orchidaceae family ID
        'quality_grade': 'research',
        'photos': 'true',
        'geo': 'true'
    })
    
    # Create reciprocal project linkage
    create_inat_project("Five Cities Orchid Atlas")
```

### Data Exchange
- **Send**: Verified orchid identifications and educational content
- **Receive**: Citizen science observations and photos
- **Schedule**: Weekly sync for new observations
- **API**: iNaturalist REST API v1

### Implementation Checklist
- [ ] Create "Orchid Atlas" iNaturalist project
- [ ] Develop iNat observation import pipeline
- [ ] Create identification assistance tool
- [ ] Set up educational content sharing
- [ ] Establish expert reviewer network

---

## 🗺️ Map of Life (MOL) Species Range Data

### Purpose
Global species distribution mapping and range modeling.

### Integration Strategy
```python
# Feed range data to Map of Life
def contribute_to_mol():
    mol_api = "https://api.mol.org/v1/"
    
    # Aggregate occurrence points by species
    for species in get_distinct_species():
        occurrences = get_occurrence_points(species)
        range_polygon = generate_range_polygon(occurrences)
        
        mol_client.submit_range_data({
            'taxon': species,
            'geometry': range_polygon,
            'source': 'Five Cities Orchid Society',
            'confidence': calculate_confidence(occurrences)
        })
```

### Data Exchange
- **Send**: High-quality occurrence points and range polygons
- **Receive**: Global species distribution models
- **Schedule**: Quarterly range updates
- **Format**: GeoJSON with metadata

### Implementation Checklist
- [ ] Register with Map of Life as data contributor
- [ ] Develop range modeling algorithms
- [ ] Create occurrence quality filtering
- [ ] Set up automated range submissions
- [ ] Integrate MOL range maps into Atlas display

---

## 🛡️ Conservation Status Integration (IUCN/CITES/OCA)

### Purpose
Conservation assessment and protection status tracking.

### Integration Strategy
```python
# Multi-source conservation status
def update_conservation_status():
    for orchid in OrchidRecord.query.all():
        # IUCN Red List status
        iucn_status = check_iucn_red_list(orchid.scientific_name)
        
        # CITES appendix listing
        cites_status = check_cites_database(orchid.scientific_name)
        
        # Orchid Conservation Alliance priority
        oca_status = check_oca_priority(orchid.scientific_name)
        
        orchid.conservation_data = {
            'iucn_status': iucn_status,
            'cites_appendix': cites_status,
            'oca_priority': oca_status,
            'last_updated': datetime.now()
        }
```

### Data Sources
- **IUCN Red List API**: Global conservation status
- **CITES Species+ Database**: Trade regulation status  
- **Orchid Conservation Alliance**: Orchid-specific priorities
- **Regional Red Lists**: Local conservation assessments

### Implementation Checklist
- [ ] Integrate IUCN Red List API
- [ ] Connect to CITES Species+ database
- [ ] Partner with Orchid Conservation Alliance
- [ ] Create conservation status display
- [ ] Set up monthly status updates

---

## 📧 Citizen Science Email Intake (Modern EOL-style)

### Purpose
Streamlined public contribution system for orchid photos and data.

### Integration Strategy
```python
# Email-based contribution system
def process_citizen_submission(email_message):
    # Parse email components
    sender = email_message.sender
    attachments = email_message.attachments
    location = extract_location_from_text(email_message.body)
    
    # AI-powered processing
    for photo in attachments:
        if is_orchid_photo(photo):
            ai_identification = identify_orchid_species(photo)
            metadata = extract_exif_data(photo)
            
            # Create pending submission
            submission = CitizenSubmission(
                contributor_email=sender,
                image_file=photo,
                ai_identification=ai_identification,
                location_info=location,
                status='pending_review'
            )
            
            # Queue for expert review
            queue_for_expert_review(submission)
```

### Workflow
1. **Email Submission**: contributors@orchidatlas.org
2. **AI Pre-processing**: Automatic species identification
3. **Expert Review**: Volunteer expert validation
4. **Integration**: Approved records added to main database
5. **Feedback**: Automated response to contributor

### Implementation Checklist
- [ ] Set up dedicated email server
- [ ] Create AI identification pipeline
- [ ] Build expert review interface
- [ ] Develop contributor feedback system
- [ ] Create submission guidelines and templates

---

## 🔄 Data Synchronization Schedule

### Daily Operations
- **WFO Taxonomy Sync**: Validate new names and updates
- **iNaturalist Check**: Import research-grade observations
- **Quality Control**: Run automated data validation

### Weekly Operations  
- **GBIF Preparation**: Compile new records for monthly export
- **Citizen Science**: Process email submissions
- **Expert Review**: Validate pending identifications

### Monthly Operations
- **GBIF Publication**: Export full DwC-A and publish
- **Conservation Updates**: Refresh IUCN/CITES status
- **Statistics Reporting**: Generate partnership metrics

### Quarterly Operations
- **Map of Life**: Submit updated range models
- **Partnership Review**: Assess data exchange quality
- **System Optimization**: Performance and accuracy improvements

---

## 📊 Success Metrics

### Data Quality Indicators
- **Taxonomic Accuracy**: % of names validated against WFO
- **Geographic Precision**: Average coordinate uncertainty
- **Image Quality**: % of research-grade photos
- **Expert Validation**: % of AI identifications confirmed

### Partnership Impact
- **GBIF Downloads**: Citations of published dataset
- **iNaturalist Engagement**: Project member growth
- **Conservation Outcomes**: Species assessments influenced
- **Citizen Contributions**: Public submissions processed

### Technical Performance
- **Sync Success Rate**: % of automated updates completed
- **Data Freshness**: Average age of external data
- **System Uptime**: Availability for data exchange
- **Processing Speed**: Time from submission to publication

---

## 🚀 Implementation Priority

### Phase 1 (Immediate - 1 month)
1. **Darwin Core Export** - Complete DwC-A system
2. **WFO Integration** - Nightly taxonomy validation
3. **GBIF Registration** - Become official data publisher

### Phase 2 (Short-term - 3 months)  
1. **iNaturalist Project** - Launch citizen science initiative
2. **Conservation Integration** - IUCN/CITES status display
3. **Email Intake** - Modern submission system

### Phase 3 (Medium-term - 6 months)
1. **Map of Life** - Range modeling contribution
2. **Advanced Analytics** - Cross-platform insights
3. **API Development** - Public data access

### Phase 4 (Long-term - 12 months)
1. **Real-time Sync** - Live data exchange
2. **Predictive Modeling** - Conservation prioritization
3. **Global Integration** - Full biodiversity network participation

---

## 📞 Partnership Contacts

### Primary Liaisons
- **GBIF**: helpdesk@gbif.org
- **iNaturalist**: help@inaturalist.org  
- **WFO**: info@worldfloraonline.org
- **Map of Life**: contact@mol.org
- **IUCN**: redlist@iucn.org

### Technical Support
- **Darwin Core**: tdwg-content@lists.tdwg.org
- **GBIF IPT**: gbif-ipt@googlegroups.com
- **API Development**: Platform-specific developer forums

This guide provides the roadmap for transforming the Orchid Atlas into a globally integrated biodiversity resource, contributing to conservation science while leveraging the collective knowledge of the international orchid community.