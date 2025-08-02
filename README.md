# Clickstream Analytics Server

A comprehensive Django-based server for collecting, processing, and analyzing user behavior data from e-commerce websites. This system tracks user interactions, provides real-time analytics, and enables targeted marketing through intelligent user segmentation and conversion prediction.

## Overview

This clickstream server is designed to capture and analyze user behavior on e-commerce platforms, particularly Shopify stores. It provides real-time insights into user interactions, conversion patterns, and enables personalized marketing campaigns through advanced analytics and machine learning.

## Key Features

### 📊 Real-time Event Tracking
- Captures user interactions (page views, clicks, cart additions, purchases)
- Session management with intelligent session detection
- Real-time event processing with Celery workers

### 🎯 User Segmentation & Analytics
- Identified user management with cross-device tracking
- Advanced user segmentation based on behavior patterns
- Conversion funnel analysis (visits → carts → purchases)
- Product-level analytics and recommendations

### 🤖 AI-Powered Features
- **Sale Notification System**: ML-powered conversion prediction using TensorFlow
- Event classification and sequence analysis
- Intelligent user scoring and targeting

### 📈 Business Intelligence
- Real-time dashboards for key metrics
- Product performance analytics
- User journey analysis
- Conversion rate optimization insights

### 🔗 E-commerce Integration
- Shopify webhook support for purchase tracking
- Product catalog synchronization
- Customer data integration
- Marketing automation APIs

## Technology Stack

### Backend Framework
- **Django 4.1+** - Web framework
- **Django REST Framework** - API development
- **Python 3.8+** - Core language

### Database & Caching
- **MySQL** - Primary database with read replicas
- **Redis** - Caching and session storage
- **Celery** - Asynchronous task processing

### Machine Learning & AI
- **TensorFlow 2.x** - Conversion prediction models
- **TensorFlow Serving** - Model inference API
- **NumPy/Pandas** - Data processing
- **Scikit-learn** - Feature engineering

### Message Queue & Processing
- **RabbitMQ** - Message broker for Celery
- **Celery Beat** - Scheduled task execution
- Multi-threaded processing for high throughput

### Deployment & Infrastructure
- **NGINX** - Web server and load balancer
- **Gunicorn** - WSGI HTTP Server
- **Ubuntu Server** - Operating system
- **SSL/HTTPS** - Security

### Monitoring & Logging
- Custom logging framework
- Performance monitoring
- Error tracking and alerting

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Load Balancer  │    │   Django App    │
│   (Websites)    │◄──►│     (NGINX)     │◄──►│    Server       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TensorFlow    │    │     Redis       │    │     MySQL       │
│    Serving      │◄──►│    (Cache)      │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Celery      │    │    RabbitMQ     │    │   Celery Beat   │
│    Workers      │◄──►│  (Message Queue)│◄──►│   (Scheduler)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Applications

### 📍 Events App
- Real-time event ingestion
- Session management
- Purchase tracking
- Shopify webhook integration

### 📊 Analytics App
- Conversion metrics
- User behavior analysis
- Product performance tracking
- Dashboard APIs

### 🔔 Notification App
- AI-powered sale notifications
- Conversion prediction models
- A/B testing framework
- Real-time scoring

### 👥 Segments App
- User segmentation APIs
- Behavioral targeting
- Customer journey mapping
- Marketing automation

### 📈 API Result App
- Data aggregation
- User profiling
- Product recommendations
- Performance optimization

## API Endpoints

### Event Tracking
```
POST /events/                    # Track user events
POST /events/purchase/           # Record purchases
POST /events/add_cart/          # Track cart additions
POST /events/shopify_webhook_purchase/  # Shopify webhooks
```

### Analytics
```
GET /analytics/session_count/          # Session metrics
GET /analytics/user_count/             # User metrics
GET /analytics/visit_conversion/       # Conversion rates
GET /analytics/product_visits/         # Product analytics
```

### User Segments
```
GET /segments/identified-users-list    # User segmentation
GET /segments/identified-users-sessions # Session-based segments
```

### Recommendations
```
GET /api/crowd_favorites/         # Popular products
GET /api/featured_collection/     # Personalized recommendations
GET /api/pick_up_where_you_left_off/  # Continue browsing
```

## Machine Learning Features

### Conversion Prediction Model
- **Input**: User behavior sequences (event types, timing)
- **Model**: LSTM neural network for sequence prediction
- **Output**: Purchase probability scores
- **Serving**: TensorFlow Serving for real-time inference

### Event Classification
- Automatic categorization of user actions
- Session boundary detection
- Behavioral pattern recognition

## Installation & Setup

### Prerequisites
```bash
- Python 3.8+
- MySQL 8.0+
- Redis 6.0+
- RabbitMQ 3.8+
- Node.js (for frontend integration)
```

### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd clickstream_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database
cp auth/mysql.cnf.example auth/mysql.cnf
# Edit mysql.cnf with your database credentials

# Run migrations
python manage.py migrate

# Start Celery workers
celery -A clickserver worker -l info

# Start Celery beat scheduler
celery -A clickserver beat -l info

# Start Django development server
python manage.py runserver
```

### Production Deployment
```bash
# Install and configure NGINX
# Set up Gunicorn with systemd
# Configure SSL certificates
# Set up monitoring and logging
```

## Configuration

### Environment Variables
```bash
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=mysql://user:pass@host:port/db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=amqp://guest@localhost//
```

### Database Configuration
- Configure read replicas for analytics queries
- Set up proper indexing for high-performance queries
- Regular backups and archival strategies

## Performance & Scalability

### Optimizations
- **Database**: Proper indexing, query optimization, read replicas
- **Caching**: Redis for session data and frequent queries
- **Async Processing**: Celery for heavy computations
- **Load Balancing**: NGINX for distributing requests

### Monitoring
- Real-time performance metrics
- Database query monitoring
- Error tracking and alerting
- Resource utilization monitoring

## Security Features

- CORS configuration for cross-origin requests
- CSRF protection (disabled for API endpoints)
- SSL/HTTPS enforcement
- Input validation and sanitization
- Rate limiting for API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

---

**Note**: This is a production-ready system handling real-time user data. Ensure proper security measures and data privacy compliance before deployment.
