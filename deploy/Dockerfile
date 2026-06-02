# Use a lightweight, secure base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application script
COPY src/app.py .

# Run the script with unbuffered output so logs appear instantly
CMD ["python", "-u", "app.py"]
