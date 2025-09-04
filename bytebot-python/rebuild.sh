#!/bin/bash
set -e

echo "🚀 Stop all services..."
docker-compose -f docker/docker-compose.yml down

echo "🚀 Building all services..."
docker-compose -f docker/docker-compose.yml build --no-cache

echo "🚀 Starting all services..."
docker-compose -f docker/docker-compose.yml up -d