FROM python:3.12.11

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is sent directly to the terminal.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# time-logger app config
ENV DB_FILE="db/time_logger.db"

# uvicorn server startup args
# --host 0.0.0.0: Makes the server accessible from outside the container.
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT=8000
ENV UVICORN_ARGS=""

# USER 1001:1001

# Expose the port that the FastAPI application will listen on.
# This informs Docker that the container listens on the specified network ports at runtime.
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn.
# We use the "exec" form of CMD for proper signal handling (e.g., graceful shutdowns).
# "main:app" refers to the 'app' object in 'main.py'.
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host $UVICORN_HOST --port $UVICORN_PORT $UVICORN_ARGS"]
