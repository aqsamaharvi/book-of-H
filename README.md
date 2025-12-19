# FastAPI Hello World Application

A minimal FastAPI application with a single endpoint that returns "Hello World".

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation


1. **Clone the repository**
```bash
git clone https://github.com/aqsamaharvi/book-of-H.git
cd book-of-H
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

The API will be available at:
- **API**: http://localhost:8001
- **Interactive API docs**: http://localhost:8001/docs
- **Alternative docs**: http://localhost:8001/redoc

## 📡 API Endpoint

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/` | Returns Hello World message | `{"message": "Hello World"}` |

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

Or with verbose output:

```bash
pytest -v
```

## 📁 Project Structure

```
book-of-H/
├── main.py              # FastAPI application
├── test_main.py         # Unit tests
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## 🛠️ Development

The application uses:
- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server with auto-reload in development
- **Pytest**: Testing framework

### Running in Production

For production, use:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 License

MIT License

## 👥 Author

aqsamaharvi

## 🏗️ Architecture

This application follows a **layered architecture** with clear separation of concerns:

```
app/
├── api/              # API Layer
│   └── v1/           # API Version 1
│       ├── endpoints.py    # Route handlers
│       └── router.py       # Router configuration
├── core/             # Core Application
│   ├── config.py     # Configuration management
│   └── logging.py    # Logging setup
├── middleware/       # Custom Middleware
│   └── request_logging.py
├── schemas/          # Pydantic Models
│   └── response.py   # Response schemas
├── services/         # Business Logic Layer
│   └── message_service.py
└── main.py           # FastAPI application factory
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- **API Layer**: Handles HTTP requests/responses
- **Service Layer**: Contains business logic
- **Schemas**: Data validation and serialization
- **Core**: Configuration and utilities

### 2. **Dependency Injection**
- Settings injected via `get_settings()`
- Service dependencies clearly defined
- Easy to test and mock

### 3. **Configuration Management**
- Environment-based configuration using Pydantic Settings
- Type-safe settings with validation
- Centralized configuration in `app/core/config.py`

### 4. **Logging & Monitoring**
- Structured logging throughout the application
- Request/response logging middleware
- Performance tracking with X-Process-Time header

### 5. **API Versioning**
- Clear API versioning strategy (`/api/v1/`)
- Easy to maintain multiple versions
- Backward compatibility support

### 6. **Error Handling**
- Centralized error handling
- Consistent error responses
- Proper HTTP status codes

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip or poetry

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd <project-directory>
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

**Development mode with auto-reload:**
```bash
python main.py
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once the application is running, access:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🧪 Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## 📡 API Endpoints

### Root
- `GET /` - Application information

### API v1
- `GET /api/v1/` - Welcome message
- `GET /api/v1/hello/{name}` - Personalized greeting
- `GET /api/v1/health` - Health check

## 🔧 Configuration

Configuration is managed through environment variables. See `.env.example` for available options:

- `APP_NAME`: Application name
- `APP_VERSION`: Application version
- `DEBUG`: Debug mode (True/False)
- `HOST`: Server host
- `PORT`: Server port
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins

## 📦 Project Structure Benefits

### ✅ Scalability
- Easy to add new endpoints, services, and features
- Clear structure for team collaboration
- Modular design allows independent development

### ✅ Maintainability
- Code organization follows industry standards
- Easy to locate and update specific functionality
- Clear dependencies between layers

### ✅ Testability
- Each layer can be tested independently
- Service layer isolated from HTTP concerns
- Easy to mock dependencies

### ✅ Reusability
- Services can be used across multiple endpoints
- Schemas ensure consistent data structures
- Middleware applies cross-cutting concerns

## 🛠️ Future Enhancements

- [ ] Database integration (SQLAlchemy)
- [ ] Authentication & Authorization (JWT)
- [ ] Rate limiting
- [ ] Caching (Redis)
- [ ] Background tasks (Celery)
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Docker containerization
- [ ] CI/CD pipeline

## 📝 License

[Your License Here]

## 👥 Contributing

[Contributing Guidelines]
