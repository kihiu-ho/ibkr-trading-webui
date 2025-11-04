# Database Setup Guide

## Overview

This application requires an external PostgreSQL database. The local PostgreSQL container has been removed to allow you to use any external database service (Neon, AWS RDS, DigitalOcean, etc.).

## Quick Start

### 1. Create a `.env` file

Create a `.env` file in the project root directory:

```bash
touch .env
```

### 2. Add your DATABASE_URL

Add the following to your `.env` file:

```env
# Database Configuration - REQUIRED
DATABASE_URL=postgresql+psycopg2://username:password@host:port/database?sslmode=require

# Example for Neon:
# DATABASE_URL=postgresql+psycopg2://user:password@ep-example.us-east-1.aws.neon.tech/dbname?sslmode=require

# Example for local PostgreSQL (if running separately):
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ibkr_trading

# Other Configuration (Optional - has defaults)
IBKR_ACCOUNT_ID=DU1234567
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
OPENAI_API_KEY=your_openai_api_key_here
```

## Database URL Format

The DATABASE_URL can use any of these formats (all will be automatically converted to use psycopg2):

```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require
postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require
postgresql+psycopg2://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require
```

**Note**: The application will automatically convert to `postgresql+psycopg2://` to use the correct driver.

### Components:

- **Protocol**: `postgresql://` or `postgresql+psycopg2://` (auto-converted if needed)
- **Username**: Your database username
- **Password**: Your database password (URL-encode special characters)
- **Host**: Database server hostname or IP
- **Port**: Database port (usually 5432)
- **Database**: Database name
- **SSL Mode**: `?sslmode=require` (recommended for external databases)

### Examples:

#### Neon Database
```
DATABASE_URL=postgresql+psycopg2://neondb_owner:npg_E0Vv5TaJSqZu@ep-restless-bush-adc0o6og-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
```

#### AWS RDS
```
DATABASE_URL=postgresql+psycopg2://admin:mypassword@mydb.123456789.us-east-1.rds.amazonaws.com:5432/ibkr_trading?sslmode=require
```

#### DigitalOcean Managed Database
```
DATABASE_URL=postgresql+psycopg2://doadmin:password@db-cluster-do-user-123456-0.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

#### Local PostgreSQL (running outside Docker)
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/ibkr_trading
```

**Note**: Use `host.docker.internal` instead of `localhost` when connecting from Docker to your host machine's database.

## Database Schema Initialization

The application will automatically create the necessary tables on first startup. Make sure your database exists and the user has appropriate permissions:

```sql
-- Required permissions
GRANT CREATE, CONNECT ON DATABASE your_database TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

## Troubleshooting

### Error: "DATABASE_URL is required"

Make sure:
1. The `.env` file exists in the project root
2. The `.env` file contains `DATABASE_URL=...`
3. The DATABASE_URL is not empty

### Error: "ModuleNotFoundError: No module named 'psycopg'"

Your DATABASE_URL might be using the wrong driver. The application expects `psycopg2-binary`.

**Solution**: The application will automatically convert these formats:
- `postgresql://` → `postgresql+psycopg2://`
- `postgresql+psycopg://` → `postgresql+psycopg2://`

Just restart the container after updating the validator code.

### Error: "DATABASE_URL must use postgresql+psycopg2:// driver"

This means your DATABASE_URL is using an unsupported format.

**Supported formats** (all auto-converted):
- `postgresql://...`
- `postgresql+psycopg://...`
- `postgresql+psycopg2://...`

The validator will automatically fix the format for you!

### Error: "password authentication failed"

- Check your username and password are correct
- Ensure special characters in the password are URL-encoded (e.g., `@` becomes `%40`)

### Error: "could not connect to server"

- Verify the hostname and port are correct
- Check if your database service is running
- Ensure firewall rules allow connections from your IP
- For Docker: Use `host.docker.internal` instead of `localhost` to connect to host machine

### Testing Database Connection

You can test your database connection using `psql`:

```bash
# Extract connection details from your DATABASE_URL and test
psql "postgresql://username:password@host:port/database?sslmode=require"
```

Or use Docker to test:

```bash
docker run --rm -it postgres:15 psql "YOUR_DATABASE_URL"
```

## Running the Application

Once your `.env` file is configured:

```bash
# Start all services
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f backend
```

The backend service will fail to start if DATABASE_URL is not properly configured.

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **Yes** | None | PostgreSQL connection string |
| `IBKR_ACCOUNT_ID` | No | `DU1234567` | Interactive Brokers account ID |
| `MINIO_ACCESS_KEY` | No | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | No | `minioadmin` | MinIO secret key |
| `OPENAI_API_KEY` | No | `your_key_here` | OpenAI API key for LLM features |

## Migrating from Local PostgreSQL

If you were using the local PostgreSQL container before:

1. **Export your data** (if needed):
   ```bash
   docker exec ibkr-postgres pg_dump -U postgres ibkr_trading > backup.sql
   ```

2. **Import to new database**:
   ```bash
   psql "YOUR_NEW_DATABASE_URL" < backup.sql
   ```

3. **Update `.env`** with new DATABASE_URL

4. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up
   ```

## Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use strong passwords** - Especially for production databases
3. **Enable SSL** - Always use `sslmode=require` for external databases
4. **Rotate credentials** - Regularly update database passwords
5. **Limit permissions** - Database user should only have necessary permissions
6. **Use connection pooling** - Already configured in the application

## Support

For issues:
1. Check the troubleshooting section above
2. Review application logs: `docker-compose logs backend`
3. Verify database connectivity outside of the application
4. Check database service status and logs

