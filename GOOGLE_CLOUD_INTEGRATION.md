# Google Cloud Integration for Orchid Continuum

## Overview
This document provides comprehensive setup instructions for the unified Google Cloud integration system that enables the complete data flow: SVO Scraper → Database + Google Sheets → Google Drive → AI Analysis.

## Architecture
```
SVO Enhanced Scraper
        ↓
   Database Storage
        ↓
  Google Sheets Sync
        ↓
  Google Drive Upload  
        ↓
   AI Analysis & Export
```

## Required Environment Variables

### 1. GOOGLE_SERVICE_ACCOUNT_JSON
**Required**: Yes  
**Description**: Complete Google Service Account credentials in JSON format  
**Purpose**: Enables Google Sheets and Google Drive API access  

**How to obtain:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable APIs: Google Sheets API, Google Drive API
4. Create Service Account (IAM & Admin > Service Accounts)
5. Generate and download JSON key file
6. Copy entire JSON content into this environment variable

**Example format:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@your-project.iam.gserviceaccount.com",
  "client_id": "12345678901234567890",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account%40your-project.iam.gserviceaccount.com"
}
```

### 2. GOOGLE_DRIVE_FOLDER_ID
**Required**: Yes  
**Description**: Google Drive folder ID where orchid images will be uploaded  
**Purpose**: Organizes all uploaded orchid images in a specific folder  

**How to obtain:**
1. Create a folder in Google Drive for orchid images
2. Share the folder with your service account email (from JSON above)
3. Copy folder ID from URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

**Example**: `1aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789`

### 3. SESSION_SECRET
**Required**: Yes  
**Description**: Flask session secret for CSRF protection  
**Purpose**: Secures admin routes that trigger data flow operations  

**How to generate:**
```python
import secrets
print(secrets.token_hex(32))
```

**Security note**: Use a random 64-character hexadecimal string

## Admin Routes for Google Cloud Integration

### 1. Trigger Unified Data Flow
**Endpoint**: `POST /admin/unified-data-flow`  
**Purpose**: Execute complete SVO → Sheets → Drive → AI pipeline  
**CSRF**: Required  

**Parameters:**
- `enable_svo_scraping`: Enable SVO data collection (default: true)
- `enable_data_sync`: Enable database + sheets sync (default: true)  
- `enable_image_processing`: Enable Google Drive uploads (default: true)
- `enable_ai_analysis`: Enable AI analysis (default: true)
- `genus`: Target orchid genus (default: 'Sarcochilus')
- `year_start`: Start year for scraping (default: 2020)
- `year_end`: End year for scraping (default: 2024)
- `max_pages`: Maximum pages to scrape (default: 5)

### 2. Test Google Cloud Integration  
**Endpoint**: `POST /admin/test-google-cloud-integration`  
**Purpose**: End-to-end testing of Sheets and Drive functionality  
**CSRF**: Required  

**Test Coverage:**
- Environment variable validation
- Google Sheets write test
- Google Drive upload test
- Permission verification

### 3. Google Cloud Status
**Endpoint**: `GET /admin/google-cloud-status`  
**Purpose**: Real-time status of Google Cloud integration  
**CSRF**: Not required (read-only)

**Response includes:**
- Environment variable status
- Integration availability
- Current data flow status
- Error details (if any)

## Security Policies

### Google Drive File Sharing
- **Access Level**: Anyone with link (read-only)
- **Discovery**: Disabled (files not searchable)
- **Metadata**: Includes upload timestamp and source
- **Organization**: All files stored in designated folder
- **Cleanup**: Automated cleanup policies can be implemented

### CSRF Protection
- All admin POST routes require valid CSRF tokens
- Tokens generated automatically by Flask-WTF
- Protection against cross-site request forgery attacks

## Testing the Integration

### Manual Testing Steps

1. **Environment Setup Test**:
   ```bash
   curl -X GET http://localhost:5000/admin/google-cloud-status
   ```

2. **Google Cloud Integration Test**:
   ```bash
   curl -X POST http://localhost:5000/admin/test-google-cloud-integration \
     -d "csrf_token=YOUR_CSRF_TOKEN"
   ```

3. **Full Data Flow Test**:
   ```bash
   curl -X POST http://localhost:5000/admin/unified-data-flow \
     -d "csrf_token=YOUR_CSRF_TOKEN" \
     -d "genus=Dendrobium" \
     -d "max_pages=2"
   ```

### Expected Outcomes

**Successful Integration Test:**
```json
{
  "success": true,
  "test_results": {
    "environment_check": {"status": "success"},
    "sheets_test": {"status": "success", "sheet_name": "OrchidContinuum_Test_20250916_123456"},
    "drive_test": {"status": "success", "drive_url": "https://drive.google.com/uc?id=..."}
  }
}
```

**Successful Data Flow:**
```json
{
  "success": true,
  "pipeline_id": "unified_flow_20250916_123456",
  "stages_completed": ["svo_harvesting", "data_sync", "image_processing", "ai_analysis"],
  "summary": {
    "total_orchids_processed": 25,
    "sheets_records_created": 25,
    "drive_images_uploaded": 18,
    "ai_analyses_completed": 25
  }
}
```

## Troubleshooting

### Common Issues

**1. "Google Cloud integration not available"**
- Check GOOGLE_SERVICE_ACCOUNT_JSON is valid JSON
- Verify service account has proper API permissions
- Ensure Google Sheets and Drive APIs are enabled

**2. "Failed to write to sheet"**
- Verify service account email has edit access to sheets
- Check if sheet name conflicts with existing sheets
- Ensure Google Sheets API quota is not exceeded

**3. "Failed to upload to Drive"**
- Verify service account has write access to folder
- Check GOOGLE_DRIVE_FOLDER_ID is correct
- Ensure Google Drive API quota is not exceeded

**4. "Invalid CSRF token"**
- Ensure SESSION_SECRET is set
- Use proper CSRF token in admin requests
- Check if session has expired

### Logging and Monitoring

**Key Log Messages:**
- `🌤️ Google Cloud Integration initialized`
- `✅ Google Cloud services initialized successfully` 
- `📊 Created new sheet: [name] with headers`
- `📸 Uploaded image to Drive: [filename] -> [url]`
- `🚀 Starting unified orchid breeding data flow pipeline`

**Error Indicators:**
- `❌ Failed to initialize Google Cloud services`
- `❌ Failed to upload image to Drive`
- `❌ Pipeline failed`

### Performance Considerations

- **Batch Operations**: Process in batches to avoid API rate limits
- **Caching**: Google Sheets are cached to reduce API calls
- **Retry Logic**: Built-in retry for transient failures
- **Timeouts**: Reasonable timeouts for all external API calls

## Integration with Existing Systems

### SVO Enhanced Scraper
- Automatically configured when Google integration is available
- Images uploaded to Drive during scraping process
- Hybrid data synchronized to Google Sheets

### AI Breeder Pro Widget
- Uses Google integration for analysis storage
- Breeding data automatically backed up to Sheets
- Generated images uploaded to Drive

### Database Models
- OrchidRecord: Enhanced with google_drive_id field
- All data synchronized between local DB and Google Sheets
- Maintains data consistency across systems

## Production Deployment

### Prerequisites Checklist
- [ ] Google Cloud Project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled  
- [ ] Service Account created with proper permissions
- [ ] Google Drive folder created and shared
- [ ] Environment variables configured
- [ ] CSRF protection enabled
- [ ] SSL/HTTPS configured (recommended)

### Monitoring
- Use `/admin/google-cloud-status` for health checks
- Monitor log files for integration errors
- Set up alerts for API quota limits
- Regular testing with `/admin/test-google-cloud-integration`

### Backup Strategy
- Google Sheets serve as primary backup for orchid data
- Google Drive provides backup for all images
- Local database remains primary source of truth
- Automated sync ensures consistency

## Support and Maintenance

For issues with Google Cloud integration:
1. Check environment variables with status endpoint
2. Run integration test to identify specific failures
3. Review logs for detailed error messages
4. Verify Google Cloud API quotas and permissions
5. Contact system administrator if issues persist

Last updated: September 16, 2025