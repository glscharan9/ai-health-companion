#!/bin/sh
# startup.sh

# This script ensures the database is ready before starting the server.

# Run the database initialization function from our Python script
echo "Initializing database..."
python -c 'from backend_server import init_db; init_db()'

# Start the Gunicorn server to serve the application
# Use the PORT environment variable provided by Render, defaulting to 5001 for local dev
echo "Starting Gunicorn server on port ${PORT:-5001}..."
exec gunicorn --bind 0.0.0.0:${PORT:-5001} backend_server:app
