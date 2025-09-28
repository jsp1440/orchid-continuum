# 🌺 The Orchid Continuum - Digital Platform

A comprehensive research-grade digital platform focused on orchid research and community management, integrating authoritative taxonomy databases, AI-powered image analysis, and ecological pattern correlation discovery.

## 🚀 Features

- **AI-Powered Orchid Identification** - Advanced image analysis using multiple AI models
- **Master AI Widget Manager** - Autonomous monitoring and optimization of all system components
- **Breeding Analysis** - Comprehensive AI-powered breeding compatibility analysis
- **Growing Condition Matching** - Personalized orchid recommendations based on location and setup
- **Health Diagnostics** - AI-powered orchid health assessment and care recommendations
- **Adaptive Care Calendars** - Intelligent care scheduling based on species and conditions
- **Authentication System** - Advanced orchid verification and anti-fraud detection
- **Comprehensive Database** - 5,888+ orchid records with advanced search and filtering

## 🏗️ Architecture

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with spatial extensions
- **Task Queue**: Celery with Redis
- **AI Services**: OpenAI GPT-4, Anthropic Claude, Google Gemini
- **Storage**: Object storage (S3/R2/GCS) with CDN
- **Deployment**: Docker containers with health checks

## 🛠️ Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/orchid-continuum.git
   cd orchid-continuum
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   alembic upgrade head
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

The application will be available at `http://localhost:8080`

## 🌐 Production Deployment

### Option 1: Google Cloud Run

1. **Set up Google Cloud**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and deploy**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/orchid-continuum
   gcloud run deploy --image gcr.io/YOUR_PROJECT_ID/orchid-continuum --platform managed
   ```

### Option 2: Fly.io

1. **Install Fly CLI and deploy**
   ```bash
   fly launch
   fly deploy
   ```

### Option 3: Render

1. **Connect repository to Render**
2. **Set environment variables**
3. **Deploy from dashboard**

## 🔧 Configuration

### Required Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - Flask session secret key
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `REDIS_URL` - Redis connection for task queue

### Optional Environment Variables

- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `GOOGLE_API_KEY` - Google services API key
- `AWS_ACCESS_KEY_ID` - AWS S3 credentials
- `SENDGRID_API_KEY` - Email service

See `.env.example` for complete configuration options.

## 🧠 AI Widget Manager

The Master AI Widget Manager provides:

- **Real-time monitoring** of all system components
- **Automated issue detection** and resolution
- **User feedback analysis** with sentiment analysis
- **Performance optimization** suggestions
- **Daily admin reports** with actionable insights

Access the dashboard at `/ai-widget-manager/dashboard`

## 📊 API Documentation

### Widget APIs

- `POST /api/orchid-health-diagnostic` - AI health diagnosis
- `POST /api/growing-condition-matcher` - Find optimal orchids for conditions
- `POST /widgets/ai-breeder-pro` - Advanced breeding analysis
- `POST /api/care-calendar` - Generate adaptive care schedules
- `POST /api/orchid-authentication` - Verify orchid authenticity

### Admin APIs

- `GET /ai-widget-manager/api/widget-status` - System health status
- `POST /ai-widget-manager/api/submit-feedback` - Submit user feedback
- `GET /ai-widget-manager/api/daily-report` - Get system reports

## 🔄 Task Queue

Background tasks are handled by Celery:

- **Widget health monitoring** - Every 5 minutes
- **Feedback processing** - Every 15 minutes  
- **Performance analysis** - Every 30 minutes
- **Improvement suggestions** - Every hour
- **Daily reports** - Daily at 6 AM

## 🗄️ Database

### Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backup

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## 📈 Monitoring

- **Health checks**: `/health` and `/ready` endpoints
- **Metrics**: Application metrics via built-in monitoring
- **Logs**: Structured logging with correlation IDs
- **Alerts**: Critical issue notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Open a GitHub issue
- Check the documentation
- Review the AI Widget Manager dashboard for system status

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Advanced AI model training
- [ ] Multi-language support
- [ ] Enhanced geographic mapping
- [ ] Research collaboration features