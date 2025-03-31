# Chat Application

A real-time chat application with voice messaging capabilities, built with Django and Redis.

## Features

- Real-time messaging
- Voice messages
- Incoming call ringtones
- User profiles
- WebSocket support via Daphne

## Prerequisites

- Python 3.x
- Redis server (or Redis Cloud for production)
- Docker and Kubernetes (for deployment)

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/bibek1414/chat-application.git
cd chat-application
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Redis

For local development, install and run Redis server:

```bash
# Ubuntu
sudo apt-get install redis-server
sudo service redis-server start

# macOS (using Homebrew)
brew install redis
brew services start redis

# Windows
# Download and install from https://github.com/microsoftarchive/redis/releases
```

### 5. Environment Variables

Create a `.env` file in the project root:

```
DEBUG=True
SECRET_KEY=your_secret_key
REDIS_URL=redis://localhost:6379/0
```

For Redis Cloud in production:
```
REDIS_URL=redis://username:password@host:port
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Start the development server

```bash
python manage.py runserver
```

For WebSocket support with Daphne:

```bash
daphne -b 0.0.0.0 -p 8000 chat_project.asgi:application
```

## Docker Setup

### Build the Docker image

```bash
docker build -t chat-app .
```

### Run the container

```bash
docker run -p 8000:8000 -d chat-app
```

## Kubernetes Deployment

Deploy the application to Kubernetes:

```bash
kubectl apply -f deployment.yml
kubectl apply -f service.yml
```

## Project Structure

```
├── chat/                  # Main chat application
├── chat_project/          # Django project settings
├── media/                 # User uploaded files (voice messages, etc.)
├── static/                # Static files
├── staticfiles/           # Collected static files
├── theme/                 # UI theme files
├── Dockerfile             # Docker configuration
├── deployment.yml         # Kubernetes deployment configuration
├── service.yml            # Kubernetes service configuration
├── entrypoint.sh          # Docker entrypoint script
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
