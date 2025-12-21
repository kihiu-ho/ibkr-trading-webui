# Multi-stage build for optimized IBKR Gateway Docker image
# Stage 1: Download and prepare gateway files (cached layer)
FROM debian:bookworm-slim AS gateway-downloader

# Install minimal tools for downloading
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /tmp

# Download IBKR Gateway (this layer will be cached unless the gateway is updated)
RUN curl -L -o clientportal.gw.zip \
    https://download2.interactivebrokers.com/portal/clientportal.gw.zip \
    && unzip clientportal.gw.zip -d /tmp/gateway \
    && rm clientportal.gw.zip

# Stage 2: Runtime image with minimal dependencies
FROM eclipse-temurin:17-jre-jammy AS runtime

# Install only essential runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r ibkr && useradd -r -g ibkr -s /bin/bash ibkr

WORKDIR /app

# Copy gateway files from downloader stage
COPY --from=gateway-downloader /tmp/gateway ./gateway/
COPY --chown=ibkr:ibkr conf.yaml ./gateway/root/conf.yaml
COPY --chown=ibkr:ibkr start.sh ./

# Copy application files (only what's needed)
COPY --chown=ibkr:ibkr webapp ./webapp/
COPY --chown=ibkr:ibkr scripts ./scripts/

# Make start script executable
RUN chmod +x start.sh

# Set proper ownership
RUN chown -R ibkr:ibkr /app

# Switch to non-root user
USER ibkr

# Health check: gateway responds (401 pre-auth is OK)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sk https://localhost:5055/v1/api/tickle >/dev/null || exit 1

# Expose ports
EXPOSE 5055 5056

# Use exec form for better signal handling
CMD ["./start.sh"]
