# Real-Time Chat Application

A production-ready real-time chat application built with Python, Django, Django REST Framework, Django Channels, and Redis. Features include user authentication with JWT, WebSocket-based real-time messaging, Redis caching for fast message retrieval, API throttling, comprehensive logging, and full test coverage.

## 🚀 Features

### Core Features
- ✅ **User Management**: Registration, login, logout with JWT authentication
- ✅ **Real-time Messaging**: WebSocket-based chat using Django Channels
- ✅ **Fast Message Retrieval**: Redis caching for instant message loading
- ✅ **Database Fallback**: PostgreSQL for persistent storage
- ✅ **API Throttling**: Rate limiting (1 message/second per user per conversation)
- ✅ **Comprehensive Logging**: Structured logging with file rotation
- ✅ **Health Monitoring**: Health check endpoint for service status
- ✅ **Full Test Coverage**: Unit and integration tests
- ✅ **CI/CD Pipeline**: GitHub Actions for automated testing
- ✅ **Docker Support**: Fully containerized with Docker Compose

### Security Features
- JWT token-based authentication
- Token blacklisting on logout
- Password validation (strength requirements)
- Email validation
- Authorization checks for conversations
- CORS support for frontend integration

## 📋 Tech Stack

- **Backend Framework**: Django 4.2+ & Django REST Framework
- **Real-time**: Django Channels 4.0+ with Daphne ASGI server
- **Caching/Messaging**: Redis
- **Database**: PostgreSQL 13+
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │─────▶│   Daphne    │─────▶│  PostgreSQL │
│ (WebSocket/ │      │   (ASGI)    │      │  (Messages) │
│    HTTP)    │      │             │      └─────────────┘
└─────────────┘      │  - Django   │
                     │  - Channels │      ┌─────────────┐
                     │  - Redis    │─────▶│    Redis    │
                     │             │      │   (Cache &  │
                     └─────────────┘      │  Channels)  │
                                          └─────────────┘
```

## 📦 Installation & Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd test-pythondeveloper
   ```

2. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```

3. **Apply database migrations** (in a new terminal):
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create a superuser** (optional):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

The application will be available at:
- **API**: `http://localhost:8000/api/`
- **Admin Panel**: `http://localhost:8000/admin/`
- **Health Check**: `http://localhost:8000/health/`

## 🔧 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication Endpoints

#### 1. Register User
```http
POST /api/users/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### 2. Login
```http
POST /api/users/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### 3. Refresh Token
```http
POST /api/users/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 4. Logout
```http
POST /api/users/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 5. Get User Profile
```http
GET /api/users/profile/
Authorization: Bearer <access_token>
```

### Conversation Endpoints

#### 1. Create Conversation
```http
POST /api/chat/conversations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "participants": [2, 3]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "participants": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    {
      "id": 2,
      "username": "janedoe",
      "email": "jane@example.com",
      "first_name": "Jane",
      "last_name": "Doe"
    }
  ],
  "messages": [],
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 2. List User's Conversations
```http
GET /api/chat/conversations/
Authorization: Bearer <access_token>
```

#### 3. Get Conversation Details
```http
GET /api/chat/conversations/{id}/
Authorization: Bearer <access_token>
```

#### 4. Get Conversation Messages
```http
GET /api/chat/conversations/{id}/messages/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "conversation_id": 1,
  "messages": [
    {
      "id": 1,
      "sender_id": 1,
      "sender": "johndoe",
      "content": "Hello!",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "source": "redis"
}
```

### WebSocket Connection

#### Connect to Chat
```
ws://localhost:8000/ws/chat/{conversation_id}/
```

**Authentication**: Include JWT token in session or use query parameters

**Send Message:**
```json
{
  "message": "Hello, this is a test message!"
}
```

**Receive Message:**
```json
{
  "message_id": 123,
  "message": "Hello, this is a test message!",
  "sender_id": 1,
  "sender": "johndoe",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Error Response (Throttled):**
```json
{
  "error": "You are sending messages too fast. Please wait a moment."
}
```

### Health Check
```http
GET /health/
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": true,
  "redis": true
}
```

## 🧪 Testing

### Run Tests
```bash
# Inside Docker container
docker-compose exec web python manage.py test

# With coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### Test Coverage
The project includes comprehensive tests for:
- User registration with validation
- Authentication (login/logout)
- JWT token management
- Conversation CRUD operations
- Message retrieval from Redis and database
- Authorization checks
- Health check endpoints
- API throttling

## 📊 Logging

Logs are stored in the `logs/` directory:
- `django.log`: General Django logs
- `api.log`: API-specific logs (requests, errors, etc.)

Log format:
```
[LEVEL] TIMESTAMP MODULE FUNCTION - MESSAGE
```

Example:
```
[INFO] 2024-01-01 12:00:00 chat consumers receive - Message saved - User: johndoe, Conversation: 1
```

## 🔐 Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DJANGO_SETTINGS_MODULE=chat_project.settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=chat_db
POSTGRES_USER=chat_user
POSTGRES_PASSWORD=chat_password
POSTGRES_HOST=db

REDIS_HOST=redis
```

## 📈 Performance & Scalability

### Redis Caching Strategy
- Messages are stored in Redis lists (FIFO)
- Last 100 messages per conversation cached
- 24-hour TTL for Redis entries
- Automatic fallback to PostgreSQL

### Throttling
- 1 message per second per user per conversation
- Implemented using Redis timestamps
- Configurable in `chat/consumers.py` (`THROTTLE_RATE_SECONDS`)

## 🚢 Deployment

### Docker Deployment
The application is production-ready with Docker. Simply:
```bash
docker-compose up -d
```

### Cloud Deployment Options
- **Heroku**: Use `heroku.yml` or container registry
- **AWS**: ECS with RDS (PostgreSQL) and ElastiCache (Redis)
- **Google Cloud**: Cloud Run with Cloud SQL and Memorystore
- **Azure**: Container Instances with Azure Database and Azure Cache

## 🛠️ Development

### Project Structure
```
test-pythondeveloper/
├── chat/                   # Chat app (conversations, messages, WebSocket)
├── users/                  # User app (authentication, profiles)
├── chat_project/           # Project settings and configuration
│   ├── settings.py
│   ├── asgi.py            # ASGI configuration for Channels
│   ├── middleware.py      # Custom middleware (logging)
│   └── views.py           # Health check
├── logs/                   # Application logs
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions small and focused

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is created as a technical assessment.

## 👨‍💻 Author

**Ivan**

## 🐛 Known Issues & Future Improvements

### Planned Improvements
- [ ] Message pagination
- [ ] File/image sharing
- [ ] Typing indicators
- [ ] Read receipts
- [ ] Group chat naming
- [ ] User online status
- [ ] Message search functionality
- [ ] Push notifications

## 📞 Support

For questions or issues, please open an issue in the repository.
