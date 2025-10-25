# Interactive Brokers Web API

## Video Walkthrough

https://www.youtube.com/watch?v=CRsH9TKveLo

## Requirements

* Docker Desktop - https://www.docker.com/products/docker-desktop/
* External PostgreSQL Database (Neon, AWS RDS, etc.) - See [Database Setup Guide](DATABASE_SETUP.md)

## Quick Start

### 1. Clone the source code
```bash
git clone https://github.com/hackingthemarkets/interactive-brokers-web-api.git
cd interactive-brokers-web-api
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and set your DATABASE_URL (REQUIRED)
# See DATABASE_SETUP.md for detailed instructions
nano .env  # or use your preferred editor
```

**Important**: You MUST set a valid `DATABASE_URL` in your `.env` file before starting the application.

Example:
```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname?sslmode=require
OPENAI_API_BASE=https://api.openai.com/v1  # or https://turingai.plus/v1 for TuringAI
OPENAI_API_KEY=your_key_here
IBKR_ACCOUNT_ID=DU1234567
```

See [OpenAI API Configuration Guide](OPENAI_API_CONFIGURATION.md) for using TuringAI or other OpenAI-compatible providers.

### 3. Bring up the container
```
docker-compose up
```

## Getting a command line prompt

```
docker exec -it ibkr bash
```
