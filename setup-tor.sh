#!/bin/bash

# ShadowLedger Tor Hidden Service Setup Script

set -e

echo "🔐 Setting up Tor hidden services for ShadowLedger..."

# Create necessary directories
mkdir -p tor/data/shadowledger_p2p
mkdir -p tor/data/shadowledger_api
mkdir -p data logs

# Set proper permissions
chmod 700 tor/data/shadowledger_p2p
chmod 700 tor/data/shadowledger_api

echo "📁 Directories created successfully"

# Start Tor service to generate hidden service keys
echo "🚀 Starting Tor service to generate hidden service keys..."
docker-compose -f docker-compose.production.yml up -d tor

# Wait for Tor to start and generate keys
echo "⏳ Waiting for Tor to generate hidden service keys..."
sleep 10

# Get the .onion addresses
if [ -f "tor/data/shadowledger_p2p/hostname" ]; then
    P2P_ONION=$(cat tor/data/shadowledger_p2p/hostname)
    echo "✅ P2P Hidden Service: $P2P_ONION"
    echo "$P2P_ONION" > tor/p2p_hostname
else
    echo "❌ Failed to generate P2P hidden service"
    exit 1
fi

if [ -f "tor/data/shadowledger_api/hostname" ]; then
    API_ONION=$(cat tor/data/shadowledger_api/hostname)
    echo "✅ API Hidden Service: $API_ONION"
    echo "$API_ONION" > tor/api_hostname
else
    echo "❌ Failed to generate API hidden service"
    exit 1
fi

echo ""
echo "🎉 Tor hidden services setup complete!"
echo ""
echo "📋 Your ShadowLedger .onion addresses:"
echo "   P2P Network: $P2P_ONION:8888"
echo "   API Access:  $API_ONION:8000"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Keep these addresses private for maximum anonymity"
echo "   - Share only with trusted users"
echo "   - Never expose these addresses on clearnet"
echo ""
echo "🚀 To start your ShadowLedger node:"
echo "   docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "🔧 To start with mining:"
echo "   docker-compose -f docker-compose.production.yml --profile mining up -d" 