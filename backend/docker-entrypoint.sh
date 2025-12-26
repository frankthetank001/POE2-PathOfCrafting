#!/bin/bash
set -e

echo "Starting PoE2 PathOfCrafting Backend..."

# Wait a moment for any dependencies to be ready
sleep 2

# Start the application
echo "Starting uvicorn server..."
exec "$@"
