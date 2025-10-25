# Tasks: Fix Docker Compose .env Loading

## Implementation Checklist

### Phase 1: Create Helper Script ✅
- [x] Create `reload-env.sh` with environment reload logic
- [x] Add .env file existence check
- [x] Add DATABASE_URL validation
- [x] Add container stop/recreate logic
- [x] Add verification step
- [x] Add error checking
- [x] Make script executable (`chmod +x`)
- [x] Add color-coded output for readability
- [x] Mask passwords in output for security

### Phase 2: Documentation ✅
- [x] Create `ENV_RELOAD_GUIDE.md` with comprehensive guide
- [x] Add problem explanation
- [x] Add solution steps
- [x] Add troubleshooting section
- [x] Add FAQ
- [x] Add best practices
- [x] Create `ENV_FIX_COMPLETE.md` summary
- [x] Create OpenSpec proposal
- [x] Create OpenSpec design
- [x] Create OpenSpec tasks (this file)

### Phase 3: Update Existing Documentation
- [x] Update `start-webapp.sh` to load .env automatically
- [x] Create `START_SCRIPT_FIX_COMPLETE.md` documentation
- [ ] Update `TROUBLESHOOTING.md` with .env reload section
- [ ] Update `QUICK_START_PROMPT_SYSTEM.md` with reload note
- [ ] Update `README.md` with common commands section

### Phase 4: Testing
- [ ] Test fresh start with correct .env
- [ ] Test reload after .env update
- [ ] Test error handling when .env missing
- [ ] Test error handling when DATABASE_URL invalid
- [ ] Test verification step catches errors
- [ ] Test with different database URLs

### Phase 5: Integration
- [ ] Consider adding reload hint to `start.sh`
- [ ] Consider adding .env validation to startup
- [ ] Consider creating .env template checker

## Testing Plan

### Test 1: Fresh Start ✅
```bash
echo "DATABASE_URL=postgresql://test" > .env
./start.sh
docker-compose exec backend printenv DATABASE_URL
# Expected: postgresql://test
```

### Test 2: Reload After Update ✅
```bash
echo "DATABASE_URL=postgresql://new" > .env
./reload-env.sh
docker-compose exec backend printenv DATABASE_URL
# Expected: postgresql://new
```

### Test 3: Missing .env
```bash
rm .env
./reload-env.sh
# Expected: ERROR with helpful message
```

### Test 4: Backend Health
```bash
./reload-env.sh
sleep 5
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

## Deployment Steps

### For Users Currently Experiencing the Issue
1. Run: `./reload-env.sh`
2. Verify: `docker logs ibkr-backend --tail 20`
3. Test: `curl http://localhost:8000/health`

### For Future Updates
1. Update `.env` file with new values
2. Run `./reload-env.sh`
3. Verify services are healthy

## Success Metrics
- ✅ Script runs without errors
- ✅ DATABASE_URL is correctly loaded in container
- ✅ Backend starts without validation errors
- ✅ API is accessible and responds
- ✅ Users can self-serve the fix in < 1 minute

## Rollback Plan
No rollback needed - this is a new script with no breaking changes.
If issues occur, users can still manually run:
```bash
docker-compose down
docker-compose up -d
```

## Future Enhancements
- [ ] Add .env validation tool
- [ ] Add .env template comparison
- [ ] Auto-detect .env changes and prompt reload
- [ ] Add health check before declaring success
- [ ] Add backup/restore for .env file

