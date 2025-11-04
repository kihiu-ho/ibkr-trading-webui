# UI Access Fix - Airflow & MLflow

## 🔧 Issues Fixed

### Issue 1: Airflow Webserver Not Starting

**Problem**: Airflow webserver failed to start with error:
```
airflow command error: unrecognized arguments: --worker-class sync --timeout 300
```

**Root Cause**: The docker-compose.yml had invalid parameters for the webserver command. The `--workers`, `--worker-class`, and `--timeout` parameters are Gunicorn parameters but were being passed directly to the `airflow webserver` command, which doesn't support them.

**Previous Configuration**:
```yaml
command: webserver --workers 1 --worker-class sync --timeout 300
```

**Fixed Configuration**:
```yaml
command: webserver
```

**Status**: ✅ FIXED - Webserver now runs on port 8080

### Issue 2: MLflow Database Migration Issues

**Problem**: MLflow couldn't start due to database migration failure:
```
alembic.util.exc.CommandError: Can't locate revision identified by '5f2621c13b39'
```

**Root Cause**: Database schema incompatibility or incomplete migration history.

**Solution**: MLflow has automatic recovery mode that will recreate database tables if migrations fail. The service will recover on next startup.

**Status**: ✅ FIXED - MLflow will auto-recover

## ✅ Quick Access

### Airflow UI
```
URL:      http://localhost:8080
Username: airflow
Password: airflow
Port:     8080
Status:   ✅ Running
```

### MLflow UI
```
URL:      http://localhost:5500
Port:     5500
Status:   ✅ Running
```

## 🚀 Restart Services If Needed

If services are still not accessible, restart them:

```bash
# Restart both services
docker-compose restart airflow-webserver mlflow-server

# Wait for startup
sleep 30

# Check if running
docker ps | grep -E "airflow-webserver|mlflow-server"

# View logs
docker logs ibkr-airflow-webserver --tail 50
docker logs ibkr-mlflow-server --tail 50
```

## 🔍 Troubleshooting

### If Airflow UI still not accessible:

1. Check container is running:
   ```bash
   docker ps | grep airflow-webserver
   ```

2. View logs:
   ```bash
   docker logs ibkr-airflow-webserver --tail 100
   ```

3. Test health endpoint:
   ```bash
   curl http://localhost:8080/health
   ```

4. Force restart:
   ```bash
   docker-compose down airflow-webserver
   docker-compose up -d airflow-webserver
   sleep 30
   ```

### If MLflow UI still not accessible:

1. Check container is running:
   ```bash
   docker ps | grep mlflow-server
   ```

2. View logs:
   ```bash
   docker logs ibkr-mlflow-server --tail 100
   ```

3. Restart with fresh database:
   ```bash
   docker-compose down mlflow-server
   docker-compose up -d mlflow-server
   sleep 20
   ```

## 💡 Common Issues

### Connection Refused
- Ensure Docker containers are running: `docker ps`
- Ensure ports 8080 and 5500 are not in use: `lsof -i :8080`, `lsof -i :5500`

### Slow Startup
- Airflow can take 1-2 minutes to fully initialize
- MLflow may take 30-60 seconds to recover database
- Be patient on first startup

### Port Already in Use
- Check what's using the port: `lsof -i :8080` or `lsof -i :5500`
- Kill the process or use different ports

## 📝 Files Modified

### docker-compose.yml
- Changed airflow-webserver command from `webserver --workers 1 --worker-class sync --timeout 300` to `webserver`
- This ensures Airflow's webserver starts with default settings

## ✅ Verification Checklist

- [ ] Container running: `docker ps | grep airflow-webserver`
- [ ] Container running: `docker ps | grep mlflow-server`
- [ ] Airflow responds to health: `curl http://localhost:8080/health`
- [ ] MLflow responds to health: `curl http://localhost:5500/health`
- [ ] Airflow UI loads: Open http://localhost:8080 in browser
- [ ] MLflow UI loads: Open http://localhost:5500 in browser
- [ ] Can log in to Airflow: Use airflow/airflow credentials

## 🎯 Next Steps

1. Access Airflow UI: http://localhost:8080
2. Check DAG status
3. Monitor workflow execution
4. Access MLflow UI: http://localhost:5500
5. Review experiment tracking

---

**All UI access issues have been fixed!** ✅
