# The Orchid Continuum - Production Scaffold

A production-ready scaffolding for The Orchid Continuum research platform, featuring neutral field names and placeholder implementations that protect proprietary workflows while providing a complete, deployable system.

## 🌺 Architecture Overview

This monorepo contains:

- **API Service** - FastAPI with auth, rate limiting, and core endpoints
- **AI Worker** - Celery-based AI processing with EXIF, embeddings, and identification stubs  
- **Ingest Service** - Data source integration with retry/backoff mechanisms
- **Embeddable Widgets** - UMD bundles for Orchid of Day, Weather Compare, and Map Viewer
- **Admin UI** - Curator dashboard with keyboard shortcuts and review queue
- **Database** - PostgreSQL with PostGIS + pgvector extensions

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Poetry (for Python dependency management)
- Node.js 18+ (for widget building)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd orchid-continuum-scaffold
   ```

2. **Environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Start services**:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Build widgets**:
   ```bash
   cd apps/widgets
   node build.js
   ```

5. **Access the application**:
   - API: http://localhost:8000
   - Admin UI: http://localhost/admin
   - Widget Demo: http://localhost/widgets/demo.html
   - API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
orchid-continuum-scaffold/
├── apps/
│   ├── widgets/          # Embeddable web components
│   │   ├── src/         # Widget source files
│   │   ├── dist/        # Built UMD bundles
│   │   └── build.js     # Build script
│   └── admin/           # Curator dashboard
├── services/
│   ├── api/             # FastAPI service
│   ├── ai-worker/       # AI processing workers
│   └── ingest/          # Data ingestion service
├── infra/
│   ├── docker/          # Dockerfiles
│   └── nginx/           # Nginx configuration
├── docs/
│   ├── public/          # Public documentation
│   └── internal/        # Internal runbooks
└── scripts/             # Utility scripts
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost/orchid_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT secret key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `SENTRY_DSN` | Sentry error tracking | Optional |
| `OTEL_ENDPOINT` | OpenTelemetry endpoint | Optional |

### Database Setup

The system requires PostgreSQL with PostGIS and pgvector extensions:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```

## 🎨 Widget Integration

### Embedding Widgets

Include the UMD bundle and use the web components:

```html
<script src="https://cdn.example.com/orchid-widgets.umd.js"></script>

<!-- Orchid of the Day -->
<orchid-of-day 
    data-theme="light" 
    data-size="medium"
    api-base="https://api.orchidcontinuum.org">
</orchid-of-day>

<!-- Weather Compare -->
<weather-compare 
    data-theme="light"
    orchid-id="123">
</weather-compare>

<!-- Map Viewer -->
<map-viewer 
    data-theme="light"
    data-zoom="3">
</map-viewer>
```

### Widget Attributes

All widgets support:
- `data-theme`: "light" or "dark"
- `api-base`: API endpoint URL
- `data-*`: Various widget-specific options

## 🔐 Authentication & Authorization

The system implements role-based access control:

- **Viewer**: Read-only access
- **Member**: Basic interactions
- **Contributor**: Can submit records
- **Curator**: Can review and approve
- **Admin**: Full system access

### API Authentication

```python
# Get access token
response = requests.post('/auth/login', {
    'email': 'user@example.com',
    'password': 'password'
})
token = response.json()['access_token']

# Use token in requests
headers = {'Authorization': f'Bearer {token}'}
```

## 🤖 AI Services

### Available Stubs

- **EXIF Parser**: Extract metadata from images
- **Embedding Generator**: Create vector embeddings for search
- **Identification Pipeline**: AI-powered species identification
- **Morphometric Analyzer**: Extract measurements from images

### Extending AI Workers

The AI workers are designed as stubs with placeholder implementations. To add proprietary logic:

1. Implement the interface methods in `services/ai-worker/main.py`
2. Add model loading and inference code
3. Configure Celery tasks for your specific workflows

## 📊 Admin Interface

### Curator Dashboard Features

- **Review Queue**: Approve, flag, or merge records
- **Keyboard Shortcuts**: J/K navigation, A/F/M actions
- **Real-time Updates**: Optimistic UI with error handling
- **Analytics**: Collection statistics and quality metrics

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `J` / `K` | Navigate next/previous |
| `A` | Approve record |
| `F` | Flag for review |
| `M` | Merge records |
| `R` | Reload current view |

## 🚢 Deployment

### Railway

1. Connect your repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy with automatic builds

### Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Initialize and deploy
fly launch
fly deploy
```

### Docker Production

```bash
# Build images
docker build -f infra/docker/Dockerfile.api -t orchid-api .
docker build -f infra/docker/Dockerfile.ai-worker -t orchid-ai-worker .
docker build -f infra/docker/Dockerfile.ingest -t orchid-ingest .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🔒 Secrecy & Disclosure Policy

This scaffold is designed to protect proprietary information:

### Public-Safe Information
- General platform features and capabilities
- Impact statistics and record counts
- Educational and conservation applications
- Widget embedding and usage examples

### Protected Information
- Database schema and table structures
- Integration workflows and pipelines
- AI processing logic and algorithms
- Source code implementation details

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=services

# Lint code
poetry run black services/
poetry run isort services/
poetry run flake8 services/
```

## 📈 Observability

### Monitoring Setup

- **Sentry**: Error tracking and performance monitoring
- **OpenTelemetry**: Distributed tracing
- **Prometheus**: Metrics collection
- **Health Checks**: Automated service monitoring

### Metrics Available

- Request counts and durations
- Database query performance
- AI processing times
- Widget interaction tracking

## 🔧 Development Tools

### Widget Development

```bash
cd apps/widgets
node build.js      # Build UMD bundles
open dist/demo.html # Preview widgets
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### API Documentation

OpenAPI documentation is automatically generated and available at `/docs` when running the API service.

## 🤝 Contributing

This scaffold provides the foundation for building The Orchid Continuum platform while protecting proprietary implementations. When extending:

1. Maintain the neutral field naming convention
2. Keep proprietary logic in separate, private modules
3. Document public APIs while protecting internal workflows
4. Follow the established patterns for widgets and services

## 📄 License

This scaffold is provided as a foundation for The Orchid Continuum platform. The actual implementation contains proprietary elements owned by Jeffery S. Parham.

---

## 📚 What to Customize Privately

When adapting this scaffold for production use:

### Database Schema
- Replace generic `Record` model with actual orchid-specific fields
- Add proper taxonomic relationships and validation
- Implement real geographic and ecological data structures

### AI Services
- Replace placeholder implementations with actual models
- Add real EXIF parsing and image analysis
- Implement production-ready embedding generation
- Add custom identification and morphometric algorithms

### Data Sources
- Implement actual GBIF, iNaturalist, and Flickr integrations
- Add proprietary data source connections
- Implement real-time ingestion pipelines
- Add data validation and deduplication logic

### Widget Functionality
- Connect widgets to real API endpoints
- Implement actual weather comparison algorithms
- Add real map data and visualization
- Enhance with production-ready UI/UX

### Security & Performance
- Implement production authentication system
- Add proper rate limiting and caching
- Optimize database queries and indexing
- Add comprehensive monitoring and alerting

This scaffold provides the structure and patterns while protecting the valuable intellectual property that makes The Orchid Continuum unique.