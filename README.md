# 🕵️ ShadowLedger

**ShadowLedger** is an experimental anonymous blockchain system designed to replicate the privacy and simplicity of cash in a digital form. It enables completely private peer-to-peer transactions using stealth addresses and local block validation, without revealing the user's identity.

## 🌐 Onion Explorer

A simple web explorer with a light wallet UI is accessible via the Tor network:

🔗 **Onion URL:**  
[http://qs6z6renwowvuatk3vidf6ivolany2vhr6zicpiupx4fpyfikmrxqsad.onion:5000/](http://qs6z6renwowvuatk3vidf6ivolany2vhr6zicpiupx4fpyfikmrxqsad.onion:5000/)

> ⚠️ This link only works in the [Tor Browser](https://www.torproject.org/).

## ⚙️ Features

- 🧱 Custom blockchain with anti-double-spend protection
- 🔐 Stealth (one-time) addresses and digital signatures
- 🔄 P2P mempool and block sync
- 📦 REST API for wallet operations and blockchain access
- 💡 Web-based light wallet (no download or installation required)
- 🐳 Docker support for easy deployment

## 🚀 Getting Started

Clone the repository and start the node using Docker:

```bash
git clone https://github.com/sl3dger/tx-shadownet.git
cd shadowledger
docker-compose up --build
