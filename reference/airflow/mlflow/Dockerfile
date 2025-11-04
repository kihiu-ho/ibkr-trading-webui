FROM python:3.10.16-slim-bookworm
WORKDIR /app

# Install uv for ultra-fast package management (10-100x faster than pip)
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies using uv
COPY requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r /app/requirements.txt && \
    echo "✓ Installed MLflow dependencies using uv"

# Copy the rest of the application
COPY . .

# Set the command to run your application
EXPOSE 5500
