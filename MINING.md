# ShadowLedger Mining Guide

## 🧱 Overview

ShadowLedger uses **Proof of Work (PoW)** mining with a **10 ShadowCoin reward** per block. Miners compete to find a nonce that produces a hash starting with a specific number of zeros (difficulty).

## ⚡ Mining Rewards

- **Block Reward**: 10 ShadowCoin per block
- **Difficulty**: 4 leading zeros (configurable in `block.py`)
- **Block Time**: Variable (depends on network hash rate)
- **Transaction Fees**: Currently 0 (all rewards come from block rewards)

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Start with mining enabled
docker-compose -f docker-compose.production.yml --profile mining up -d

# Or use the basic compose file
docker-compose --profile mining up -d
```

### Option 2: Manual Setup

```bash
# 1. Start the node first
python p2p.py &
python api.py &

# 2. Start mining
python miner.py --address YOUR_STEALTH_ADDRESS
```

## 🔧 Mining Configuration

### Environment Variables

```bash
# Set your mining address
export MINER_ADDRESS="shadow1yourminingaddress000000000000000000"

# Set mining difficulty (optional)
export MINING_DIFFICULTY=4

# Set mining threads (if supported)
export MINING_THREADS=4
```

### Docker Environment

```yaml
# In docker-compose.yml
miner:
  environment:
    - MINER_ADDRESS=shadow1yourminingaddress000000000000000000
    - LOG_LEVEL=INFO
    - MINING_DIFFICULTY=4
```

## 📊 Mining Statistics

### Check Mining Status

```bash
# Via CLI
python cli.py blockchain info

# Via API
curl http://localhost:8000/status

# Check logs
tail -f logs/miner.log
```

### Monitor Mining Performance

```bash
# View real-time mining logs
docker-compose logs -f miner

# Check mining statistics
curl http://localhost:8000/status | jq '.blockchain'
```

## 🎯 Mining Strategies

### 1. Solo Mining (Recommended for Privacy)

```bash
# Run your own node and mine only to it
python miner.py --address YOUR_ADDRESS --peers 127.0.0.1
```

**Advantages:**
- Complete privacy
- No pool fees
- Full control over transactions

**Disadvantages:**
- Lower chance of finding blocks
- Requires more computational power

### 2. Pool Mining (If pools exist)

```bash
# Connect to a mining pool (if available)
python miner.py --address YOUR_ADDRESS --pool POOL_ONION_ADDRESS
```

**Advantages:**
- More consistent rewards
- Lower computational requirements

**Disadvantages:**
- Reduced privacy
- Pool fees
- Centralization risk

## 🔍 Mining Difficulty

### Current Settings

- **Difficulty**: 4 leading zeros
- **Target**: Hash must start with "0000"
- **Adjustment**: Manual (can be modified in `block.py`)

### Adjusting Difficulty

```python
# In block.py
DIFFICULTY = 4  # Change this value
```

**Difficulty Levels:**
- **1**: Very easy (for testing)
- **2**: Easy
- **3**: Medium
- **4**: Current production level
- **5+**: Hard (requires significant computational power)

## 💰 Reward Distribution

### Block Reward Structure

```python
# Each mined block contains:
{
    "reward": 10,           # 10 ShadowCoin to miner
    "address": "miner_address",  # Miner's stealth address
    "txs": [...],           # Transactions from mempool
    "nonce": 12345,         # Proof of work
    "hash": "0000abc..."    # Block hash
}
```

### Reward Verification

```bash
# Check your mining rewards
python cli.py wallet balance YOUR_MINER_ADDRESS

# View recent blocks you mined
python cli.py blockchain blocks --count 10
```

## 🛠️ Advanced Mining

### Custom Mining Script

```python
#!/usr/bin/env python3
from miner import Miner
import time

# Create custom miner
miner = Miner(
    address="shadow1yourminingaddress000000000000000000",
    peers=["127.0.0.1"]  # Solo mining
)

# Start mining with custom settings
miner.start_mining()

# Monitor mining
while True:
    stats = miner.get_stats()
    print(f"Blocks mined: {stats['blocks_mined']}")
    print(f"Hashrate: {stats['total_hashrate']:.2f} H/s")
    print(f"Uptime: {stats['uptime']:.0f}s")
    time.sleep(60)
```

### Mining with Multiple Addresses

```bash
# Run multiple miners with different addresses
python miner.py --address shadow1miner1address000000000000000000 &
python miner.py --address shadow1miner2address000000000000000000 &
python miner.py --address shadow1miner3address000000000000000000 &
```

## 📈 Performance Optimization

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 2GB
- Storage: 10GB

**Recommended:**
- CPU: 4+ cores
- RAM: 4GB+
- Storage: 50GB+
- SSD for better performance

### Optimization Tips

1. **Use SSD storage** for blockchain data
2. **Increase CPU priority** for mining process
3. **Monitor system resources** during mining
4. **Use dedicated mining hardware** for better performance

## 🔒 Privacy Considerations

### Anonymous Mining

1. **Use Tor hidden services** for P2P communication
2. **Don't expose your mining address** on clearnet
3. **Use different addresses** for different purposes
4. **Rotate mining addresses** periodically

### Security Best Practices

1. **Run mining on dedicated hardware**
2. **Use firewall rules** to block unnecessary ports
3. **Monitor for suspicious activity**
4. **Keep mining software updated**

## 🚨 Troubleshooting

### Common Issues

**1. Mining not starting**
```bash
# Check if node is running
docker-compose ps

# Check logs
docker-compose logs miner
```

**2. Low hash rate**
```bash
# Check CPU usage
htop

# Verify mining configuration
cat logs/miner.log | grep "hashrate"
```

**3. No blocks found**
```bash
# Check difficulty setting
grep "DIFFICULTY" block.py

# Verify blockchain is syncing
python cli.py blockchain info
```

### Debug Commands

```bash
# Check mining status
curl http://localhost:8000/status

# View mining logs
tail -f logs/miner.log

# Test mining manually
python -c "from miner import Miner; m = Miner('test'); print('Miner ready')"
```

## 📚 Additional Resources

- [Production Deployment Guide](PRODUCTION.md)
- [API Documentation](README.md#api-documentation)
- [CLI Usage](README.md#cli-interface)

## 🆘 Support

For mining issues:
1. Check the logs: `tail -f logs/miner.log`
2. Verify configuration: `python cli.py blockchain info`
3. Test connectivity: `python cli.py network peers`

---

**Happy Mining! 🧱⚡** 