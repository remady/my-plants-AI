## 🚀 Quick Start

  

### Prerequisites

  

- Python 3.13+

- PostgreSQL ([see Database setup](#database-setup))

- Docker and Docker Compose (optional)

  

### Environment Setup

  

1. Clone the repository:

  

```bash

git  clone  <repository-url>

cd  <project-directory>

```

  

2. Create and activate a virtual environment:

  

```bash

uv  sync

```

  

3. Copy the example environment file:

  

```bash

cp  .env.example  .env.[development|staging|production]  # e.g. .env.development

```

  

4. Update the `.env` file with your configuration (see `.env.example` for reference)

  

### Database setup

  

1. Create a PostgreSQL database (e.g Supabase or local PostgreSQL)

2. Update the database connection string in your `.env` file:

  

```bash

POSTGRES_URL="postgresql://:your-db-password@POSTGRES_HOST:POSTGRES_PORT/POSTGRES_DB"

```

  

- You don't have to create the tables manually, the ORM will handle that for you.But if you faced any issues,please run the `schemas.sql` file to create the tables manually.

  

### Running the Application

  

#### Local Development

  

1. Install dependencies:

  

```bash

uv sync

```

  

2. Run the application:

  

```bash

make [dev|staging|production]  # e.g. make dev

```

  

1. Go to Swagger UI:

  

```bash

http://localhost:8000/docs

```

  

#### Using Docker

  

1. Build and run with Docker Compose:

  

```bash

make  docker-build-env  ENV=[development|staging|production]  # e.g. make docker-build-env ENV=development

make  docker-run-env  ENV=[development|staging|production]  # e.g. make docker-run-env ENV=development

```

  

2. Access the monitoring stack:

  

```bash

# Prometheus metrics

http://localhost:9090

  

# Grafana dashboards

http://localhost:3000

Default  credentials:

-  Username:  admin

-  Password:  admin

```

  

The Docker setup includes:

  

- FastAPI application

- PostgreSQL database

- Prometheus for metrics collection

- Grafana for metrics visualization

  

## Evaluations

[deepeval](https://deepeval.com/docs/getting-started) e2e metrics evaluations and [Confident AI](https://www.confident-ai.com/products/llm-evaluation) as an observability platform

### Running E2E Evaluations

 1. Create an account on [Confident AI](https://www.confident-ai.com/products/llm-evaluation)
 2. Get an API key
 3. Run command
     ```bash
     deepeval login --confident-api-key {YOUR_API_KEY}
	   ```

You can run evaluations with different options using the provided Makefile commands:

```bash

# 1st option with Confident AI report

make  eval [ENV=development|staging|production]

# or without make
deepeval test run tests -m smoke

# 2nd option without report generation. Uses pytest as a runner

make  eval-no-report [ENV=development|staging|production]

# or without make
pytest tests -m smoke

```


## 🔧 Configuration


The application uses a flexible configuration system with environment-specific settings:

-  `.env.development`


