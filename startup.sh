#!/bin/sh
# startup.sh

# This script ensures the database is ready before starting the server.

# Run the database initialization function from our Python script
echo "Initializing database..."
python -c 'from backend_server import init_db; init_db()'

# Start the Gunicorn server to serve the application
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:5001 backend_server:app
