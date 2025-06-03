# 🏢 Bonhoeffer Machines CRM Backend

A high-performance FastAPI-based backend service for the Bonhoeffer Machines CRM system, providing comprehensive APIs for lead management, user authentication, location tracking, and sales operations.

## 🚀 Features

- **🔐 Authentication & Authorization** - JWT-based secure authentication
- **👥 User Management** - Role-based access control (Admin, HR, Salesperson)
- **📈 Lead Management** - Complete lead lifecycle management
- **📍 Location Services** - Geographic lead assignment and tracking
- **📊 Analytics & Reporting** - Sales performance and territory management
- **📱 File Upload** - Profile pictures and document management
- **🌐 CORS Enabled** - Ready for cross-origin requests

## 🛠️ Tech Stack

- **Framework:** FastAPI 0.115.0
- **Database:** SQLAlchemy with SQLite/PostgreSQL support
- **Authentication:** JWT with python-jose
- **Password Hashing:** bcrypt via passlib
- **Validation:** Pydantic schemas
- **Migration:** Alembic
- **Location Services:** GeoPy integration

## ⚡ Quick Start

### Local Development

1. **Clone and Setup:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration:**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# For local development, SQLite is fine:
DATABASE_URL=sqlite:///./crm_db.sqlite
SECRET_KEY=your-super-secret-jwt-key-here
```

3. **Initialize Database:**
```bash
# Run migrations
alembic upgrade head

# Seed with sample data
python seed_data.py
```

4. **Start Development Server:**
```bash
uvicorn main:app --reload
```

5. **Access API:**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### 🚀 Vercel Deployment

This backend is ready for Vercel deployment with:
- ✅ `vercel.json` configuration
- ✅ Environment variables support
- ✅ SQLite database (production-ready)
- ✅ Static file handling
- ✅ CORS configuration

**Deploy Steps:**
1. Push to GitHub repository
2. Connect to Vercel dashboard
3. Set environment variables in Vercel:
   - `SECRET_KEY`: Your JWT secret key
   - `DATABASE_URL`: `sqlite:///./crm_db.sqlite`
4. Deploy!
```bash
# Run migrations
alembic upgrade head

# Seed initial data (optional)
python seed_data.py
```

6. **Start the server:**
```bash
python main.py
```

The API will be available at http://localhost:8000

## 📋 Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost/db` |
| `SECRET_KEY` | JWT signing secret | `your-256-bit-secret` |
| `SMTP_USERNAME` | Email service username | `notifications@company.com` |
| `SMTP_PASSWORD` | Email service password | `app-specific-password` |
| `SMTP_SERVER` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |

## 🔌 API Endpoints

### Authentication Endpoints

#### POST `/login`
Authenticate user and receive JWT token
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "role": "salesperson"
  }
}
```

#### GET `/me`
Get current authenticated user information
**Headers:** `Authorization: Bearer {token}`

### User Management Endpoints

#### POST `/users`
Create new user (Admin/HR only)
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "role": "salesperson",
  "password": "secure123"
}
```

#### GET `/users`
Get all users (Admin only)

#### PUT `/users/{user_id}`
Update user information (Admin only)

#### DELETE `/users/{user_id}`
Delete user (Admin only)

### Salesperson Endpoints

#### GET `/salespersons`
Get all salespersons with their current status

#### GET `/salespersons/nearby?lat={latitude}&lng={longitude}`
Get salespersons sorted by distance from given coordinates

#### POST `/salesperson/location`
Update salesperson's current location
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "status": "available"
}
```

### Lead Management Endpoints

#### POST `/leads`
Create new lead (CRM/Admin only)
```json
{
  "name": "Company ABC",
  "email": "contact@companyabc.com",
  "phone": "+1234567890",
  "address": "123 Business St, City, State",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "status": "new",
  "priority": "high"
}
```

#### GET `/leads`
Get all leads with pagination and filtering
**Query Parameters:**
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of records (default: 100)
- `status`: Filter by lead status
- `assigned_to`: Filter by assigned salesperson

#### PUT `/leads/{lead_id}`
Update lead information

#### DELETE `/leads/{lead_id}`
Delete lead

### Assignment Endpoints

#### POST `/assign`
Assign lead to salesperson
```json
{
  "lead_id": 1,
  "salesperson_id": 2,
  "notes": "High priority client in downtown area"
}
```

#### GET `/assignments`
Get assignments with filters
**Query Parameters:**
- `salesperson_id`: Filter by salesperson
- `status`: Filter by assignment status
- `date_from`: Start date filter
- `date_to`: End date filter

#### PUT `/assignments/{assignment_id}`
Update assignment status

### Reports Endpoints

#### GET `/reports/dashboard`
Get dashboard statistics

#### GET `/reports/leads`
Get lead conversion reports

#### GET `/reports/salesperson/{salesperson_id}`
Get individual salesperson performance

## 🗄️ Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Full name |
| email | String | Unique email address |
| password_hash | String | Bcrypt hashed password |
| role | Enum | User role (admin, executive, crm, hr, salesperson) |
| is_active | Boolean | Account status |
| created_at | DateTime | Registration timestamp |
| last_login | DateTime | Last login timestamp |

### Leads Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Company/contact name |
| email | String | Contact email |
| phone | String | Contact phone |
| address | String | Physical address |
| latitude | Float | GPS latitude |
| longitude | Float | GPS longitude |
| status | Enum | Lead status (new, contacted, qualified, closed) |
| priority | Enum | Priority level (low, medium, high) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Salesperson_Locations Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users |
| latitude | Float | Current latitude |
| longitude | Float | Current longitude |
| status | Enum | Availability status |
| updated_at | DateTime | Last location update |

### Assignments Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| lead_id | Integer | Foreign key to leads |
| salesperson_id | Integer | Foreign key to users |
| assigned_by | Integer | Foreign key to assigning user |
| status | Enum | Assignment status |
| notes | Text | Assignment notes |
| assigned_at | DateTime | Assignment timestamp |
| completed_at | DateTime | Completion timestamp |

## 🔐 Authentication & Security

### JWT Token Authentication
- Tokens expire after 30 minutes (configurable)
- Refresh tokens not implemented (stateless design)
- Password hashing using bcrypt
- Role-based access control on all endpoints

### Role Hierarchy
1. **Admin**: Full system access
2. **Executive**: Read access to all data, limited write access
3. **CRM**: Lead and assignment management
4. **HR**: User management and onboarding
5. **Salesperson**: Own assignments and location updates only

### Security Headers
- CORS configured for frontend origin
- Request rate limiting (if configured)
- Input validation using Pydantic models

## 📊 Database Migrations

### Using Alembic
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1

# View migration history
alembic history
```

### Seed Data
```bash
# Run seed script to populate initial data
python seed_data.py
```

This creates:
- 11 test users across all roles
- Sample leads with geographic data
- Initial assignments for testing

## 🧪 Testing & Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=.
```

### Development Server
```bash
# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🚨 Error Handling

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "detail": "Error message description",
  "type": "error_type",
  "code": "ERROR_CODE"
}
```

## 📈 Performance Considerations

### Database Optimization
- Indexes on frequently queried columns (email, latitude, longitude)
- Connection pooling with SQLAlchemy
- Pagination for large result sets

### Location Queries
- Spatial indexing for geographic queries
- Distance calculations using Geopy
- Caching of frequently accessed location data

## 🔧 Configuration Files

### main.py
Entry point for the FastAPI application

### database.py
Database connection and session management

### auth.py
Authentication utilities and JWT handling

### schemas.py
Pydantic models for request/response validation

### config.py
Application configuration and environment variables

## 📦 Dependencies

### Core Dependencies
- **FastAPI**: Modern web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration tool
- **Psycopg**: PostgreSQL adapter
- **Pydantic**: Data validation
- **Python-JOSE**: JWT token handling
- **Passlib**: Password hashing
- **Geopy**: Geographic calculations

### Development Dependencies
- **Pytest**: Testing framework
- **HTTPX**: HTTP client for testing
- **Uvicorn**: ASGI server

## 🚀 Deployment

### Vercel Deployment (Recommended)
This backend is fully configured for Vercel deployment.

### Production Setup
1. Set up PostgreSQL database (or use SQLite for development)
2. Configure environment variables in Vercel dashboard
3. Deploy via GitHub integration

## 📋 Vercel Deployment Checklist

### ✅ Files Ready
- [x] `vercel.json` configuration
- [x] `requirements.txt` with all dependencies
- [x] `.env.example` template
- [x] `.gitignore` excludes sensitive files
- [x] `main.py` with Vercel handler
- [x] README.md documentation

### ✅ Code Ready
- [x] CORS configured for production domains
- [x] Environment variables support
- [x] Static file handling
- [x] Database initialization
- [x] Error handling
- [x] No cache/temp files tracked

### 🚀 Deploy Now
1. **Push to GitHub**: Ensure all changes are committed
2. **Vercel Dashboard**: Import your repository
3. **Root Directory**: Set to `backend`
4. **Environment Variables**: Add in Vercel dashboard:
   ```
   SECRET_KEY=your-super-secret-key-here
   DATABASE_URL=sqlite:///./crm_db.sqlite
   ```
5. **Deploy**: Click deploy!

### 🔧 Post-Deployment
- Test API endpoints: `https://your-backend.vercel.app/docs`
- Update frontend environment variables
- Test login functionality
- Monitor logs in Vercel dashboard

## 💡 Production Tips
- Use PostgreSQL for production database
- Set strong SECRET_KEY in production
- Monitor API performance with Vercel Analytics
- Set up custom domain for professional API URL

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📞 Support

For backend-specific issues:
1. Check logs in the console output
2. Verify database connection and migrations
3. Validate environment variable configuration
4. Review API documentation at `/docs`
