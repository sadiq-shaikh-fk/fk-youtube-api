# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install necessary packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Celery for async tasks and Redis for caching
RUN pip install celery[redis]

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Default command to run Gunicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "all_routes:app", "--bind", "0.0.0.0:8000"]
