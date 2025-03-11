FROM python:3.11

ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 8000

# Add entrypoint script to handle migrations and collectstatic
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Start the app
CMD ["/entrypoint.sh"]
