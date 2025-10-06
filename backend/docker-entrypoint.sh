#!/bin/bash
set -e

echo "Starting PoE2 PathOfCrafting Backend..."

# Wait a moment for any dependencies to be ready
sleep 2

# Initialize database if it doesn't exist
if [ ! -f "/app/data/crafting.db" ]; then
    echo "Database not found. Initializing..."
    python scripts/create_tables.py
    python scripts/populate_complete_crafting_data.py
    echo "Database initialized successfully!"
else
    echo "Database already exists. Skipping initialization."
fi

# Start the application
echo "Starting uvicorn server..."
exec "$@"
