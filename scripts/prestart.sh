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
    echo "Superuser created successfully."
else
    # Check if failure was due to existing user (non-critical)
    if grep -qi "already exists\|UNIQUE constraint\|duplicate key" /tmp/superuser.log 2>/dev/null; then
        echo "Superuser already exists, continuing..."
    else
        echo "WARNING: Superuser creation failed with exit code $superuser_exit_code"
        echo "Superuser output:"
        cat /tmp/superuser.log
        echo "Continuing with startup anyway..."
    fi
fi

echo "Pre-start script finished successfully."
