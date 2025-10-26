# Implementation Tasks

## 1. Add uv to Dockerfiles
- [x] 1.1 Update `docker/Dockerfile.backend` to install and use `uv`
- [x] 1.2 Add `uv` to base image with optimized caching
- [x] 1.3 Replace `pip install` commands with `uv pip install`
- [x] 1.4 Test dependency installation performance
- [x] 1.5 Update IBKR Gateway `Dockerfile` if it has Python dependencies

## 2. Optimize Dockerfile Layer Caching
- [x] 2.1 Restructure `docker/Dockerfile.backend` for better layer caching
- [x] 2.2 Separate requirements copying from code copying
- [x] 2.3 Add `.dockerignore` to exclude unnecessary files
- [x] 2.4 Test build cache effectiveness

## 3. Enhance start-webapp.sh Script
- [x] 3.1 Add `detect_images()` function to check if images exist
- [x] 3.2 Add `--rebuild` flag to force image rebuilding
- [x] 3.3 Add `--fast` flag to skip health checks (expert mode)
- [x] 3.4 Add `--help` flag with usage documentation
- [x] 3.5 Remove `--build` from default `docker-compose up` command
- [x] 3.6 Add timing output to show startup duration
- [x] 3.7 Add informative messages about build vs no-build decisions

## 4. Update docker-compose.yml
- [x] 4.1 Add image tags for better caching (e.g., `ibkr-backend:latest`)
- [x] 4.2 Ensure all services reference consistent image names
- [x] 4.3 Verify build context paths are optimal

## 5. Create .dockerignore
- [x] 5.1 Create `.dockerignore` file in project root
- [x] 5.2 Exclude `node_modules/`, `venv/`, `.git/`, `*.pyc`, `__pycache__/`
- [x] 5.3 Exclude log files and temporary files
- [x] 5.4 Exclude documentation and markdown files

## 6. Documentation
- [x] 6.1 Update README.md with new startup flags
- [x] 6.2 Document when to use `--rebuild` vs default
- [x] 6.3 Add troubleshooting section for build issues
- [x] 6.4 Document performance improvements

## 7. Testing
- [x] 7.1 Test first-time startup with no existing images
- [x] 7.2 Test subsequent startup (should be <10 seconds)
- [x] 7.3 Test `--rebuild` flag
- [x] 7.4 Test `--fast` flag
- [x] 7.5 Test all services start correctly with new build process
- [x] 7.6 Verify `uv` installs all packages correctly
- [x] 7.7 Benchmark startup times (before/after)

## 8. Validation
- [x] 8.1 Validate OpenSpec proposal with `openspec validate optimize-docker-startup --strict`
- [x] 8.2 Ensure no regressions in functionality
- [x] 8.3 Verify Docker image sizes haven't increased significantly

