#!/bin/bash

# Run migrations
echo "Running database migrations..."
alembic upgrade head 