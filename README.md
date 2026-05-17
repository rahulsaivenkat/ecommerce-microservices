\# Ecommerce Microservices API



A production-grade ecommerce REST API built with Python and FastAPI, structured as 5 independent microservices each with its own PostgreSQL database.



\## Architecture

Client → API Gateway (port 8000)

├── Auth Service        (port 8001)

├── Products Service    (port 8002)

├── Orders Service      (port 8003)

├── Payment Service     (port 8004)

└── Notify Service      (port 8005)

Shared Infrastructure:



PostgreSQL 15 (5 separate databases)

Redis 7 (caching + pub/sub event bus)





\## Tech Stack



\- \*\*Language:\*\* Python 3.11

\- \*\*Framework:\*\* FastAPI + Pydantic v2

\- \*\*Database:\*\* PostgreSQL 15 (database-per-service pattern)

\- \*\*Cache + Messaging:\*\* Redis 7 (cache-aside + Pub/Sub)

\- \*\*Auth:\*\* JWT (python-jose) + bcrypt (passlib)

\- \*\*ORM:\*\* SQLAlchemy 2.0 async + Alembic

\- \*\*Containerization:\*\* Docker + Docker Compose

\- \*\*CI/CD:\*\* GitHub Actions



\## Services



| Service | Port | Responsibility |

|---|---|---|

| Gateway | 8000 | JWT validation, request routing |

| Auth | 8001 | Register, login, JWT tokens |

| Products | 8002 | Product catalog, inventory, Redis caching |

| Orders | 8003 | Cart management, order lifecycle |

| Payment | 8004 | Razorpay integration, transaction tracking |

| Notify | 8005 | Redis Pub/Sub consumer, email/SMS alerts |



\## Key Features



\- Event-driven architecture using Redis Pub/Sub for async inter-service communication

\- Database-per-service pattern with 5 independent PostgreSQL databases

\- JWT-based authentication with access/refresh token rotation and RBAC

\- Redis cache-aside pattern for product catalog

\- Razorpay payment gateway integration with webhook verification

\- Containerized with Docker multi-stage builds

\- Automated CI/CD via GitHub Actions



\## Local Setup



\### Prerequisites

\- Docker Desktop

\- Git



\### Run locally



```bash

\# Clone the repo

git clone <your-repo-url>

cd ecommerce



\# Create .env file

cp .env.example .env



\# Start all services

docker compose up -d



\# Check all services are running

docker compose ps

```



\### Test credentials

\- Customer: test@example.com / test1234

\- Vendor: vendor@example.com / vendor1234



\## API Endpoints



\### Auth

POST /api/v1/auth/register

POST /api/v1/auth/login

POST /api/v1/auth/refresh

POST /api/v1/auth/logout

GET  /api/v1/users/me



\### Products

GET    /api/v1/products/

GET    /api/v1/products/{id}

POST   /api/v1/products/

PUT    /api/v1/products/{id}

DELETE /api/v1/products/{id}

GET    /api/v1/products/{id}/inventory

PUT    /api/v1/products/{id}/inventory



\### Cart

GET    /api/v1/cart/

POST   /api/v1/cart/items

PUT    /api/v1/cart/items/{id}

DELETE /api/v1/cart/items/{id}



\### Orders

POST /api/v1/orders/

GET  /api/v1/orders/

GET  /api/v1/orders/{id}

PUT  /api/v1/orders/{id}/cancel



\### Payment

POST /api/v1/payment/create-order

POST /api/v1/payment/webhook

GET  /api/v1/payment/status/{order\_id}



\## Environment Variables



| Variable | Description |

|---|---|

| SECRET\_KEY | JWT signing secret |

| DATABASE\_URL | PostgreSQL connection string |

| REDIS\_URL | Redis connection string |

| RAZORPAY\_KEY\_ID | Razorpay API key |

| RAZORPAY\_WEBHOOK\_SECRET | Razorpay webhook secret |

| SMTP\_USER | Email sender address |

| SMTP\_PASSWORD | Email password |

| TWILIO\_ACCOUNT\_SID | Twilio account SID |

| TWILIO\_AUTH\_TOKEN | Twilio auth token |



\## Resume Highlights



\- Built 5 independent Python/FastAPI microservices with database-per-service pattern

\- Implemented event-driven architecture using Redis Pub/Sub decoupling order, payment, inventory and notification flows

\- Integrated Razorpay payment gateway with webhook signature verification

\- JWT authentication with refresh token rotation and role-based access control

\- Redis cache-aside pattern reducing database load on product catalog

\- Full CI/CD pipeline via GitHub Actions with automated Docker builds

\- Deployed on AWS EC2 with Docker Compose

