FROM python:3.12.11

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is sent directly to the terminal.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies.
# --no-cache-dir: Prevents pip from storing downloaded packages, reducing image size.
# --upgrade pip: Ensures pip is up-to-date.
# We explicitly install build-essential and libpq-dev here if needed by any Python packages
# (e.g., psycopg2 for PostgreSQL, or other packages requiring native compilation).
# For slim images, you often need to install these build dependencies explicitly.
#RUN apt-get update \
#    && apt-get install -y --no-install-recommends \
#        build-essential \
#        libpq-dev \
#        curl \
#    && pip install --no-cache-dir --upgrade pip \
#    && pip install --no-cache-dir -r /app/requirements.txt \
#    && apt-get remove -y build-essential libpq-dev \
#    && apt-get autoremove -y \
#    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container.
# All subsequent commands will be executed relative to this directory.
# WORKDIR /app

# Copy the requirements file into the container.
# This step is done separately to leverage Docker's layer caching.
# If only the application code changes, this layer won't be rebuilt.
COPY requirements.txt /app/requirements.txt

# Install Python dependencies.
# --no-cache-dir: Prevents pip from storing downloaded packages, reducing image size.
# --upgrade pip: Ensures pip is up-to-date.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire FastAPI application code into the container.
# This should be done after installing dependencies to benefit from layer caching.
COPY ./app /app

# time-logger app variables
ENV DB_FILE="db/time_logger.db"

# Expose the port that the FastAPI application will listen on.
# This informs Docker that the container listens on the specified network ports at runtime.
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn.
# We use the "exec" form of CMD for proper signal handling (e.g., graceful shutdowns).
# "main:app" refers to the 'app' object in 'main.py'.
# --host 0.0.0.0: Makes the server accessible from outside the container.
# --port 8000: Specifies the port to listen on.
# For production, consider using Gunicorn with Uvicorn workers for process management:
# CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
# USER 1001:1001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
