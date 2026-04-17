# Use an official Python runtime as parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY app ./app
COPY static ./static

# Expose port
EXPOSE 8000

# Run with the new app module path
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
