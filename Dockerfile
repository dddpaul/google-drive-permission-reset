# Use an official Python runtime based on Alpine as a parent image
FROM python:3.11-alpine

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY permission-reset.py /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Expose local auth server port
EXPOSE 45678

# Run script.py when the container launches
ENTRYPOINT ["python", "/app/permission-reset.py"]
