# 🛒 Ecommerce Microservices API

A production-grade ecommerce backend built with Python and FastAPI, structured as 5 independent microservices communicating via Redis Pub/Sub, secured with JWT authentication, and deployed on AWS EC2 via GitHub Actions CI/CD.

---
## Architecture

```
Client (Browser / Mobile / Postman)
            │
            ▼
    ┌───────────────┐
    │  API Gateway  │  ← JWT validation, rate limiting, request routing
    │   port 8000   │
    └───────┬───────┘
            │
   ┌────────┼────────────────────────────┐
   │        │          │        │        │
   ▼        ▼          ▼        ▼        ▼
[Auth]  [Products]  [Orders] [Payment] [Notify]
 8001     8002        8003     8004      8005
   │        │          │        │        │
   ▼        ▼          ▼        ▼        ▼
auth_db  prod_db    ord_db   pay_db   ntf_db
      (5 databases inside 1 PostgreSQL instance)

    Shared: Redis 7 — Cache + Pub/Sub Event Bus
```
---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI + Pydantic v2 |
| Database | PostgreSQL 15 (database-per-service) |
| Cache + Messaging | Redis 7 (cache-aside + Pub/Sub) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Containerization | Docker multi-stage builds + Docker Compose |
| CI/CD | GitHub Actions → AWS EC2 |
| Payment | Razorpay |
| Notifications | Twilio SMS + SMTP Email + Jinja2 templates |

---

## Services

| Service | Port | Responsibility |
|---|---|---|
| Gateway | 8000 | JWT validation, reverse proxy, route forwarding |
| Auth | 8001 | Register, login, JWT access/refresh tokens, RBAC |
| Products | 8002 | Product catalog, inventory, Redis caching |
| Orders | 8003 | Cart management, order lifecycle, background tasks |
| Payment | 8004 | Razorpay integration, webhook verification |
| Notify | 8005 | Redis Pub/Sub consumer, email + SMS notifications |

---

## Key Features

- **Event-driven architecture** — Redis Pub/Sub decouples order, payment, inventory and notification flows across services
- **Database-per-service pattern** — 5 isolated PostgreSQL databases, one per service
- **JWT authentication** — access + refresh token rotation with role-based access control (customer, vendor, admin)
- **Redis cache-aside** — product catalog cached with automatic invalidation on writes
- **API Gateway** — single entry point with JWT validation and header forwarding (X-User-ID, X-User-Role)
- **Async background tasks** — order auto-cancellation after 15-minute payment timeout using FastAPI BackgroundTasks
- **Razorpay integration** — payment order creation and webhook signature verification
- **Docker multi-stage builds** — optimized production images with non-root users
- **CI/CD pipeline** — GitHub Actions runs lint → test → build → deploy on every push to main

---

## Event Flow
Order Placed → order.created → Payment pre-creates transaction
→ Notify sends confirmation SMS
Payment Success → payment.success → Orders updates status to CONFIRMED
→ Notify sends receipt email + SMS
Order Cancelled → order.cancelled → Products restores inventory
→ Notify sends cancellation email

---

## Local Setup

### Prerequisites
- Docker Desktop
- Git

### Run locally

```bash
# Clone the repo
git clone <your-repo-url>
cd ecommerce

# Create environment file
cp .env.example .env

# Start all infrastructure + services
docker compose up -d

# Verify all containers are healthy
docker compose ps
```

### Test the API

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass1234", "full_name": "Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass1234"}'

# Get products
curl http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer <your_token>"
```

---

## API Reference

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/v1/auth/register | ❌ | Register new user |
| POST | /api/v1/auth/login | ❌ | Login, get tokens |
| POST | /api/v1/auth/refresh | ❌ | Refresh access token |
| POST | /api/v1/auth/logout | ✅ | Revoke refresh token |
| GET | /api/v1/users/me | ✅ | Get current user |

### Products
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/v1/products/ | ✅ | List products (paginated, filterable) |
| GET | /api/v1/products/{id} | ✅ | Get single product |
| POST | /api/v1/products/ | ✅ vendor/admin | Create product |
| PUT | /api/v1/products/{id} | ✅ vendor/admin | Update product |
| DELETE | /api/v1/products/{id} | ✅ vendor/admin | Soft delete product |
| GET | /api/v1/products/{id}/inventory | ✅ | Get stock level |
| PUT | /api/v1/products/{id}/inventory | ✅ vendor/admin | Update stock |

### Cart & Orders
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/v1/cart/ | ✅ | Get current cart |
| POST | /api/v1/cart/items | ✅ | Add item to cart |
| PUT | /api/v1/cart/items/{id} | ✅ | Update quantity |
| DELETE | /api/v1/cart/items/{id} | ✅ | Remove item |
| POST | /api/v1/orders/ | ✅ | Place order from cart |
| GET | /api/v1/orders/ | ✅ | List user orders |
| GET | /api/v1/orders/{id} | ✅ | Order details |
| PUT | /api/v1/orders/{id}/cancel | ✅ | Cancel order |

### Payment
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/v1/payment/create-order | ✅ | Create Razorpay order |
| POST | /api/v1/payment/webhook | ❌ | Razorpay webhook |
| GET | /api/v1/payment/status/{order_id} | ✅ | Get transaction status |

---

## Environment Variables

| Variable | Description |
|---|---|
| SECRET_KEY | JWT signing secret |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| RAZORPAY_KEY_ID | Razorpay API key ID |
| RAZORPAY_KEY_SECRET | Razorpay secret key |
| RAZORPAY_WEBHOOK_SECRET | Razorpay webhook secret |
| SMTP_HOST | SMTP server host |
| SMTP_USER | Email sender address |
| SMTP_PASSWORD | Email app password |
| TWILIO_ACCOUNT_SID | Twilio account SID |
| TWILIO_AUTH_TOKEN | Twilio auth token |
| TWILIO_PHONE_NUMBER | Twilio phone number |

---

## CI/CD Pipeline
Push to main
│
├── CI Job (runs on every push + PR)
│   ├── Lint with ruff + black
│   ├── Run pytest with 60%+ coverage
│   └── Build Docker image
│
└── Deploy Job (push to main only)
├── SSH into AWS EC2
├── git pull
├── docker compose build
├── docker compose up -d
└── Run Alembic migrations

---

## Resume Highlights

- Architected and built **5 independent FastAPI microservices** with database-per-service isolation using PostgreSQL, following industry-standard microservices patterns
- Designed an **event-driven system** using Redis Pub/Sub decoupling order, payment, inventory and notification workflows across services
- Built a **custom API Gateway** in FastAPI with JWT validation, reverse proxying, and role-based header injection
- Implemented **JWT authentication** with access/refresh token rotation, bcrypt hashing, and RBAC (customer, vendor, admin roles)
- Applied **Redis cache-aside pattern** for product catalog reducing database load with automatic cache invalidation on writes
- Containerized all services using **Docker multi-stage builds** with non-root users for security
- Delivered full **CI/CD pipeline** with GitHub Actions: lint → test → Docker build → SSH deploy to AWS EC2
- Integrated **Razorpay payment gateway** with HMAC webhook signature verification and idempotent transaction processing
- Built **async background tasks** for order auto-cancellation with 15-minute payment timeout

---

## Project Structure
ecommerce/
├── services/
│   ├── gateway/        # API Gateway
│   ├── auth/           # Authentication service
│   ├── products/       # Product catalog service
│   ├── orders/         # Orders and cart service
│   ├── payment/        # Payment service
│   └── notify/         # Notification service
├── postgres/
│   └── init.sql        # Database initialization
├── docker-compose.yml
├── .env.example
└── README.md