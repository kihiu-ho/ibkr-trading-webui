# Fix Database Setup Script Connection Issues

## Why
The `setup-databases-quick.sh` script fails to create databases automatically because it doesn't properly extract and construct the PostgreSQL connection string from the `DATABASE_URL`. It's trying to connect to a local socket instead of the external database.

## What Changes
- Fix connection string parsing to properly extract host, user, and password
- Improve error handling for missing DATABASE_URL
- Add validation before attempting database creation
- Use proper connection string format for psql
- Better error messages when connection fails

## Impact
- **Affected specs**: deployment (modified)
- **Affected code**: 
  - `setup-databases-quick.sh` - fix connection string handling
- **Benefits**: 
  - Automated database creation will work correctly
  - Better error messages
  - More reliable setup experience

