# ShadowLedger - Anonymous Blockchain on Tor Network

A privacy-focused blockchain implementation with stealth addresses, anonymous P2P networking via Tor hidden services, and enterprise-grade production deployment.

## 🌐 Onion Explorer

A simple web explorer with a light wallet UI is accessible via the Tor network:

🔗 **Onion URL:**  
[http://qs6z6renwowvuatk3vidf6ivolany2vhr6zicpiupx4fpyfikmrxqsad.onion:5000/](http://qs6z6renwowvuatk3vidf6ivolany2vhr6zicpiupx4fpyfikmrxqsad.onion:5000/)

> ⚠️ This link only works in the [Tor Browser](https://www.torproject.org/).

## 🚀 Features

- **🔐 Stealth Addresses** - Privacy-focused address generation
- **🌐 Tor Hidden Services** - Anonymous P2P networking via .onion addresses
- **⚡ FastAPI** - High-performance REST API
- **🐳 Docker Ready** - Production containerization with Tor
- **📊 Monitoring** - Comprehensive logging and metrics
- **🔒 Security** - Rate limiting, input validation, SSL/TLS
- **🛠️ CLI Tools** - Command-line interface for management
- **📈 Scalable** - Load balancing and high availability support
- **🧱 Mining** - 10 ShadowCoin reward per block with configurable difficulty

## 📦 Quick Start

### Production Deployment (Tor Network)

```bash
# 1. Clone repository
git clone <repository-url>
cd tx-shadownet

# 2. Setup Tor hidden services
chmod +x setup-tor.sh
./setup-tor.sh

# 3. Start production services
docker-compose -f docker-compose.production.yml up -d

# 4. Start with mining (optional)
docker-compose -f docker-compose.production.yml --profile mining up -d
```

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start P2P node
python p2p.py &

# Start API server
python api.py
```

## 🧱 Mining

ShadowLedger uses **Proof of Work (PoW)** with **10 ShadowCoin reward** per block.

### Quick Mining Start

```bash
# Start mining with Docker
docker-compose -f docker-compose.production.yml --profile mining up -d

# Or manually
python miner.py --address YOUR_STEALTH_ADDRESS
```

### Mining Configuration

```bash
# Set your mining address
export MINER_ADDRESS="shadow1yourminingaddress000000000000000000"

# Check mining status
python cli.py blockchain info
```

📖 **Complete Mining Guide**: [MINING.md](MINING.md)

## 🛠️ Usage

### CLI Interface

```bash
# Create wallet
python cli.py wallet create

# Get balance
python cli.py wallet balance shadow1abc123...

# Send transaction
python cli.py tx send --from addr1 --to addr2 --amount 10 --key privkey

# Get blockchain info
python cli.py blockchain info

# Start mining
python cli.py mine --address YOUR_ADDRESS
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Create wallet
curl -X POST http://localhost:8000/wallet/create

# Get balance
curl http://localhost:8000/wallet/shadow1abc123.../balance

# Send transaction
curl -X POST http://localhost:8000/transaction/send \
  -H "Content-Type: application/json" \
  -d '{"sender":"addr1","recipient":"addr2","amount":10,"private_key":"key"}'
```

## 🔐 Tor Network Setup

### Anonymous P2P Networking

ShadowLedger runs on the Tor network using hidden services (.onion addresses) for complete anonymity.

#### Your .onion Addresses

After running `./setup-tor.sh`, you'll get:
- **P2P Network**: `yourp2p.onion:8888`
- **API Access**: `yourapi.onion:8000`

#### Share Your Node

Share your .onion addresses with trusted users to build the network:
```bash
# Your node addresses (keep private)
P2P: abc123def456.onion:8888
API: xyz789ghi012.onion:8000
```

### Network Configuration

```python
# In p2p.py - Add your .onion addresses
BOOTSTRAP_NODES = [
    "abc123def456.onion",  # Your node
    "xyz789ghi012.onion",  # Another trusted node
]
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tor Network   │    │   ShadowLedger  │    │   Blockchain    │
│   (.onion)      │◄──►│   Node          │◄──►│   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hidden        │    │   API Server    │    │   Miner         │
│   Services      │    │   (FastAPI)     │    │   (PoW)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# P2P Configuration
P2P_PORT=8888
BOOTSTRAP_NODES=abc123def456.onion,xyz789ghi012.onion

# Security
RATE_LIMIT_PER_MINUTE=60
MAX_TRANSACTION_AMOUNT=1000000

# Mining
MINER_ADDRESS=shadow1yourminingaddress000000000000000000
MINING_DIFFICULTY=4
```

### Docker Configuration

```yaml
# docker-compose.production.yml
version: '3.8'
services:
  tor:
    image: dperson/torproxy:latest
    # Tor hidden services configuration
  
  shadowledger:
    build: .
    # Main node with API and P2P
  
  miner:
    build: .
    # Dedicated mining service
    profiles: [mining]
```

## 🔐 Security Features

- **Tor Hidden Services** - Anonymous networking
- **Rate Limiting** - Prevents API abuse
- **Input Validation** - Comprehensive request validation
- **SSL/TLS Support** - Secure HTTPS communication
- **Firewall Ready** - Configurable network security
- **Non-root Docker** - Secure container execution
- **Health Checks** - Automated service monitoring

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# System status
curl http://localhost:8000/status

# Network peers
curl http://localhost:8000/network/peers
```

### Logs

```bash
# View logs
tail -f logs/api.log
tail -f logs/p2p.log
tail -f logs/miner.log

# Docker logs
docker-compose logs -f
```

## 🚀 Production Deployment

For production deployment, see [PRODUCTION.md](PRODUCTION.md) for:

- Enterprise security configuration
- Load balancing setup
- SSL/TLS configuration
- Monitoring and alerting
- Backup strategies
- Performance optimization
- High availability setup

## 📚 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | System status |
| POST | `/wallet/create` | Create wallet |
| POST | `/wallet/recover` | Recover wallet |
| GET | `/wallet/{address}/balance` | Get balance |
| POST | `/transaction/send` | Send transaction |
| GET | `/transaction/{txid}` | Get transaction |
| GET | `/blockchain` | Get blockchain |
| GET | `/blockchain/latest` | Get latest block |
| GET | `/network/peers` | Get peers |

### Response Format

```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "timestamp": 1640995200
}
```

## 🧪 Testing

```bash
# Run tests
pytest

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/status

# Test CLI
python cli.py wallet create
python cli.py blockchain info

# Test mining
python miner.py --address shadow1test000000000000000000000000000000
```

## 📦 Components

### Core Modules

- **`block.py`** - Blockchain core logic
- **`transaction.py`** - Transaction handling
- **`wallet.py`** - Wallet management
- **`stealth.py`** - Stealth address generation
- **`p2p.py`** - P2P networking
- **`api.py`** - REST API server
- **`miner.py`** - Mining service
- **`cli.py`** - Command-line interface

### Production Tools

- **`Dockerfile`** - Production container
- **`docker-compose.production.yml`** - Tor-enabled orchestration
- **`setup-tor.sh`** - Tor hidden service setup
- **`start.sh`** - Production startup script
- **`PRODUCTION.md`** - Deployment guide
- **`MINING.md`** - Mining guide

## 🔄 Development

### Local Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Start development server
python api.py

# Run tests
pytest

# Format code
black .
```

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [PRODUCTION.md](PRODUCTION.md), [MINING.md](MINING.md)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## 🎯 Roadmap

- [ ] Mobile wallet app
- [ ] Web explorer improvements
- [ ] Advanced privacy features
- [ ] Cross-chain bridges
- [ ] Smart contracts
- [ ] Governance system
- [ ] Mining pools
- [ ] Advanced Tor features

---

**ShadowLedger** - Anonymous blockchain for the future 🌟🔐
