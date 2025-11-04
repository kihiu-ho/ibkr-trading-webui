FROM python:3.10.16-slim-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Install dependencies using pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application
COPY . .

# Expose MLflow server port
EXPOSE 5500

