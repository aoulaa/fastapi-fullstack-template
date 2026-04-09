#!/bin/bash

# Exit on error
set -e

echo "Starting prestart script..."

# Run migrations
echo "Running database migrations..."
if [ -f "alembic.ini" ]; then
    python -m alembic upgrade head
else
    echo "alembic.ini not found in $(pwd), skipping migrations."
fi

# Create first superuser (don't fail if it already exists)
echo "Creating first superuser..."
set +e  # Temporarily disable exit on error
python -m app.commands.create_first_superuser 2>&1 | tee /tmp/superuser.log
superuser_exit_code=$?
set -e  # Re-enable exit on error

if [ $superuser_exit_code -eq 0 ]; then
    echo "Superuser created/verified successfully."
else
    echo "ERROR: Superuser creation failed with exit code $superuser_exit_code"
    echo "Output:"
    cat /tmp/superuser.log
    exit 1
fi

echo "Pre-start script finished successfully."
