# Deployment Infrastructure Specification

## ADDED Requirements

### Requirement: Fast Docker Startup
The system SHALL provide fast startup times for developers by avoiding unnecessary Docker image rebuilds.

#### Scenario: Subsequent startup without code changes
- **GIVEN** Docker images have been built previously
- **AND** no dependency changes have occurred
- **WHEN** developer runs `./start-webapp.sh`
- **THEN** the system SHALL start in <10 seconds without rebuilding images
- **AND** all services SHALL be operational

#### Scenario: First-time startup
- **GIVEN** no Docker images exist locally
- **WHEN** developer runs `./start-webapp.sh` for the first time
- **THEN** the system SHALL build images using optimized layer caching
- **AND** the build SHALL complete in <150 seconds
- **AND** subsequent runs SHALL be fast (<10 seconds)

#### Scenario: Explicit rebuild request
- **GIVEN** developer has made dependency changes
- **WHEN** developer runs `./start-webapp.sh --rebuild`
- **THEN** the system SHALL force rebuild all images
- **AND** the system SHALL provide feedback about the rebuild process

### Requirement: Fast Python Package Installation
The system SHALL use `uv` (Astral's Rust-based package installer) for installing Python dependencies in Docker images.

#### Scenario: Installing Python dependencies during build
- **GIVEN** a Dockerfile with Python dependencies
- **WHEN** the Docker image is built
- **THEN** the system SHALL use `uv pip install` instead of `pip install`
- **AND** installation SHALL be 10-100x faster than traditional pip
- **AND** all required packages SHALL be installed correctly

#### Scenario: Dependency cache invalidation
- **GIVEN** a Docker image with cached dependency layers
- **WHEN** `requirements.txt` is modified
- **THEN** only the dependency layer SHALL be rebuilt
- **AND** system dependencies and uv installation SHALL remain cached
- **AND** application code layers SHALL remain cached

### Requirement: Optimized Docker Layer Caching
The system SHALL structure Dockerfiles to maximize layer caching efficiency.

#### Scenario: Code change without dependency change
- **GIVEN** a Docker image with properly layered caching
- **WHEN** only application code is modified
- **THEN** system dependency layers SHALL remain cached
- **AND** Python dependency layers SHALL remain cached
- **AND** only the application code layer SHALL be rebuilt
- **AND** rebuild SHALL take <30 seconds

#### Scenario: Dockerfile layer structure
- **GIVEN** a Dockerfile for backend services
- **THEN** layer 1 SHALL install system dependencies (rarely changes)
- **AND** layer 2 SHALL install uv (rarely changes)
- **AND** layer 3 SHALL install Python dependencies (changes occasionally)
- **AND** layer 4 SHALL copy application code (changes frequently)

### Requirement: Startup Script Command-Line Flags
The system SHALL provide command-line flags for controlling startup behavior.

#### Scenario: Normal startup
- **WHEN** developer runs `./start-webapp.sh` with no flags
- **THEN** images SHALL be built only if they don't exist
- **AND** all health checks SHALL be performed
- **AND** startup SHALL complete in <10 seconds if images exist

#### Scenario: Force rebuild
- **WHEN** developer runs `./start-webapp.sh --rebuild`
- **THEN** all Docker images SHALL be rebuilt regardless of existence
- **AND** the system SHALL display rebuild progress
- **AND** startup SHALL complete with fresh images

#### Scenario: Fast startup mode
- **WHEN** developer runs `./start-webapp.sh --fast`
- **THEN** health checks SHALL be skipped
- **AND** startup SHALL complete in <5 seconds
- **AND** services SHALL start without waiting for readiness

#### Scenario: Help documentation
- **WHEN** developer runs `./start-webapp.sh --help`
- **THEN** the system SHALL display usage documentation
- **AND** all available flags SHALL be documented
- **AND** example commands SHALL be provided

### Requirement: Build Status Feedback
The system SHALL provide clear feedback about build and startup operations.

#### Scenario: Informative startup messages
- **WHEN** startup script runs
- **THEN** the system SHALL display whether images exist or need building
- **AND** the system SHALL display timing information for builds
- **AND** the system SHALL display timing information for service startup
- **AND** messages SHALL use color-coded output for clarity

#### Scenario: Image detection notification
- **GIVEN** Docker images already exist
- **WHEN** developer runs `./start-webapp.sh`
- **THEN** the system SHALL display "Using cached images"
- **AND** suggest using `--rebuild` to force rebuild

### Requirement: Docker Ignore File
The system SHALL exclude unnecessary files from Docker build context using `.dockerignore`.

#### Scenario: Excluding development files
- **GIVEN** a `.dockerignore` file in the project root
- **THEN** Python cache files SHALL be excluded (`__pycache__/`, `*.pyc`)
- **AND** node modules SHALL be excluded (`node_modules/`)
- **AND** git directory SHALL be excluded (`.git/`)
- **AND** documentation files SHALL be excluded (`*.md`, `docs/`)
- **AND** log files SHALL be excluded (`logs/`, `*.log`)
- **AND** IDE files SHALL be excluded (`.vscode/`, `.idea/`)

#### Scenario: Faster build context upload
- **GIVEN** a `.dockerignore` file excluding unnecessary files
- **WHEN** Docker build runs
- **THEN** build context SHALL be smaller
- **AND** context upload SHALL be faster
- **AND** builds SHALL be more efficient

### Requirement: Consistent Image Tagging
The system SHALL use consistent image tagging for caching and versioning.

#### Scenario: Image naming in docker-compose.yml
- **GIVEN** services defined in docker-compose.yml
- **THEN** each service SHALL have an explicit image name
- **AND** image names SHALL use `:latest` tag for development
- **AND** multiple services sharing code SHALL use the same base image
- **AND** image names SHALL be referenced consistently across services

#### Scenario: Image reuse across services
- **GIVEN** multiple services (backend, celery-worker, celery-beat) using the same code
- **WHEN** images are built
- **THEN** they SHALL share the same base image (`ibkr-backend:latest`)
- **AND** only one build SHALL occur for the shared image
- **AND** services SHALL reference the built image by name

