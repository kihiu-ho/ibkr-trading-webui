# Fix Chart Generation and Add Frontend Chart Viewing

## Why

Currently experiencing multiple critical issues:

1. **Chart Generation 500 Error**: Plotly Kaleido requires Chrome/Chromium which is not installed in the Docker container, causing all chart generation requests to fail with 500 errors
2. **Tailwind CDN Warning**: Using `cdn.tailwindcss.com` in production which is not recommended and may cause performance/reliability issues
3. **No Chart Viewing UI**: Charts are generated but there's no frontend interface to view, browse, or manage them

These issues prevent users from:
- Generating technical analysis charts
- Viewing generated charts
- Managing chart lifecycle
- Having a production-ready frontend

## What Changes

### 1. Fix Chart Generation (Kaleido/Chrome Issue)
- Install Chromium in Docker backend image
- Configure Kaleido to use installed Chromium
- Add fallback to HTML-only generation if image export fails
- Add proper error handling and user feedback

### 2. Replace Tailwind CDN with Build Process
- Add Tailwind CSS as npm dependency
- Configure PostCSS build pipeline
- Generate minified production CSS
- Update base template to use built CSS

### 3. Add Chart Viewing Frontend
- Create interactive chart gallery page
- Add chart detail view with zoom/pan
- Add chart filtering by symbol, strategy, date
- Add chart generation form with indicator selection
- Add chart deletion and management
- Auto-refresh for newly generated charts

## Impact

### Affected specs
- New: `specs/chart-viewing/spec.md` - Chart viewing and management capability
- New: `specs/frontend-build/spec.md` - Frontend build process

### Affected code
- `docker/Dockerfile.backend` - Add Chromium installation
- `backend/services/chart_service.py` - Add fallback logic
- `frontend/templates/base.html` - Replace CDN with built CSS
- `frontend/templates/charts.html` - Complete redesign for viewing
- `frontend/static/css/styles.css` - New compiled Tailwind CSS
- `package.json` - New file for npm dependencies
- `tailwind.config.js` - New Tailwind configuration
- `postcss.config.js` - New PostCSS configuration

### Breaking Changes
None - all changes are additive or fix existing issues

