#!/usr/bin/env python3
"""
ShadowLedger CLI - Production-ready command line interface
"""

import argparse
import json
import sys
import os
import time
from typing import Optional
import requests
from mnemonic import Mnemonic
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from stealth import generate_stealth_keys
from transaction import get_balance, verify_signature

class ShadowLedgerCLI:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.timeout = 30
        
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make HTTP request to API"""
        try:
            url = f"{self.api_url}{endpoint}"
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            sys.exit(1)
        except json.JSONDecodeError:
            print("❌ Invalid JSON response from API")
            sys.exit(1)
    
    def create_wallet(self):
        """Create a new wallet"""
        print("🔐 Creating new wallet...")
        
        try:
            result = self._make_request("POST", "/wallet/create")
            
            print("✅ Wallet created successfully!")
            print(f"📧 Address: {result['address']}")
            print(f"🔑 Private Key: {result['private_key']}")
            print(f"🔓 Public Key: {result['public_key']}")
            print(f"📝 Mnemonic: {result['mnemonic']}")
            print("\n⚠️  IMPORTANT: Save your mnemonic and private key securely!")
            
            return result
        except Exception as e:
            print(f"❌ Failed to create wallet: {e}")
            sys.exit(1)
    
    def recover_wallet(self, mnemonic: str):
        """Recover wallet from mnemonic"""
        print("🔓 Recovering wallet from mnemonic...")
        
        try:
            result = self._make_request("POST", "/wallet/recover", {"mnemonic": mnemonic})
            
            print("✅ Wallet recovered successfully!")
            print(f"📧 Address: {result['address']}")
            print(f"🔑 Private Key: {result['private_key']}")
            print(f"🔓 Public Key: {result['public_key']}")
            
            return result
        except Exception as e:
            print(f"❌ Failed to recover wallet: {e}")
            sys.exit(1)
    
    def get_balance(self, address: str):
        """Get balance for an address"""
        print(f"💰 Getting balance for {address[:16]}...")
        
        try:
            result = self._make_request("GET", f"/wallet/{address}/balance")
            
            print(f"✅ Balance: {result['balance']} ShadowCoin")
            return result['balance']
        except Exception as e:
            print(f"❌ Failed to get balance: {e}")
            sys.exit(1)
    
    def send_transaction(self, sender: str, recipient: str, amount: float, private_key: str):
        """Send a transaction"""
        print(f"📤 Sending {amount} ShadowCoin from {sender[:16]}... to {recipient[:16]}...")
        
        try:
            data = {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "private_key": private_key
            }
            
            result = self._make_request("POST", "/transaction/send", data)
            
            print("✅ Transaction sent successfully!")
            print(f"🆔 TXID: {result['txid']}")
            print(f"💰 Amount: {result['amount']} ShadowCoin")
            print(f"📧 From: {result['sender']}")
            print(f"📧 To: {result['recipient']}")
            
            return result
        except Exception as e:
            print(f"❌ Failed to send transaction: {e}")
            sys.exit(1)
    
    def get_transaction(self, txid: str):
        """Get transaction details"""
        print(f"🔍 Getting transaction {txid[:16]}...")
        
        try:
            result = self._make_request("GET", f"/transaction/{txid}")
            
            print("✅ Transaction details:")
            print(f"🆔 TXID: {result['txid']}")
            
            if 'block_index' in result:
                print(f"📦 Block: {result['block_index']}")
                print(f"🔗 Block Hash: {result['block_hash'][:16]}...")
                print("📋 Status: Confirmed")
            else:
                print("📋 Status: Pending")
            
            tx = result['transaction']
            print(f"📧 From: {tx['from']}")
            print(f"📧 To: {tx['to']}")
            print(f"💰 Amount: {tx['amount']} ShadowCoin")
            
            return result
        except Exception as e:
            print(f"❌ Failed to get transaction: {e}")
            sys.exit(1)
    
    def get_blockchain_info(self):
        """Get blockchain information"""
        print("📊 Getting blockchain information...")
        
        try:
            result = self._make_request("GET", "/status")
            
            print("✅ Blockchain Status:")
            print(f"📦 Blocks: {result['blockchain']['length']}")
            print(f"💸 Total Transactions: {result['blockchain']['total_transactions']}")
            print(f"💰 Total Rewards: {result['blockchain']['total_rewards']}")
            print(f"🌐 Connected Peers: {result['network']['peers_count']}")
            print(f"📋 Mempool Size: {result['mempool']['size']}")
            
            if result['blockchain']['last_block_hash']:
                print(f"🔗 Latest Block: {result['blockchain']['last_block_hash'][:16]}...")
            
            return result
        except Exception as e:
            print(f"❌ Failed to get blockchain info: {e}")
            sys.exit(1)
    
    def get_latest_blocks(self, count: int = 5):
        """Get latest blocks"""
        print(f"📦 Getting latest {count} blocks...")
        
        try:
            result = self._make_request("GET", "/blockchain")
            blocks = result['blocks']
            
            if not blocks:
                print("📭 No blocks found")
                return
            
            latest_blocks = blocks[-count:] if len(blocks) >= count else blocks
            
            print(f"✅ Latest {len(latest_blocks)} blocks:")
            for block in latest_blocks:
                print(f"  📦 Block #{block['index']}: {block['hash'][:16]}...")
                print(f"    ⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block['timestamp']))}")
                print(f"    👤 Miner: {block['address'][:16]}...")
                print(f"    💰 Reward: {block['reward']} ShadowCoin")
                print(f"    📋 Transactions: {len(block.get('txs', []))}")
                print()
            
            return latest_blocks
        except Exception as e:
            print(f"❌ Failed to get latest blocks: {e}")
            sys.exit(1)
    
    def get_peers(self):
        """Get connected peers"""
        print("🌐 Getting connected peers...")
        
        try:
            result = self._make_request("GET", "/network/peers")
            
            print(f"✅ Connected Peers ({result['count']}):")
            for peer in result['peers']:
                print(f"  🌐 {peer}")
            
            return result
        except Exception as e:
            print(f"❌ Failed to get peers: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="ShadowLedger CLI - Production-ready command line interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new wallet
  python cli.py wallet create
  
  # Recover wallet from mnemonic
  python cli.py wallet recover "word1 word2 word3 ..."
  
  # Get balance
  python cli.py wallet balance shadow1abc123...
  
  # Send transaction
  python cli.py tx send --from shadow1abc123... --to shadow1def456... --amount 10 --key abc123...
  
  # Get transaction details
  python cli.py tx get abc123def456...
  
  # Get blockchain info
  python cli.py blockchain info
  
  # Get latest blocks
  python cli.py blockchain blocks --count 10
        """
    )
    
    parser.add_argument("--api-url", default="http://localhost:8000", help="API server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Wallet commands
    wallet_parser = subparsers.add_parser("wallet", help="Wallet operations")
    wallet_subparsers = wallet_parser.add_subparsers(dest="wallet_action")
    
    wallet_subparsers.add_parser("create", help="Create new wallet")
    
    recover_parser = wallet_subparsers.add_parser("recover", help="Recover wallet from mnemonic")
    recover_parser.add_argument("mnemonic", help="12-word mnemonic phrase")
    
    balance_parser = wallet_subparsers.add_parser("balance", help="Get wallet balance")
    balance_parser.add_argument("address", help="Wallet address")
    
    # Transaction commands
    tx_parser = subparsers.add_parser("tx", help="Transaction operations")
    tx_subparsers = tx_parser.add_subparsers(dest="tx_action")
    
    send_parser = tx_subparsers.add_parser("send", help="Send transaction")
    send_parser.add_argument("--from", dest="sender", required=True, help="Sender address")
    send_parser.add_argument("--to", dest="recipient", required=True, help="Recipient address")
    send_parser.add_argument("--amount", type=float, required=True, help="Amount to send")
    send_parser.add_argument("--key", dest="private_key", required=True, help="Private key")
    
    get_tx_parser = tx_subparsers.add_parser("get", help="Get transaction details")
    get_tx_parser.add_argument("txid", help="Transaction ID")
    
    # Blockchain commands
    blockchain_parser = subparsers.add_parser("blockchain", help="Blockchain operations")
    blockchain_subparsers = blockchain_parser.add_subparsers(dest="blockchain_action")
    
    blockchain_subparsers.add_parser("info", help="Get blockchain information")
    
    blocks_parser = blockchain_subparsers.add_parser("blocks", help="Get latest blocks")
    blocks_parser.add_argument("--count", type=int, default=5, help="Number of blocks to show")
    
    # Network commands
    network_parser = subparsers.add_parser("network", help="Network operations")
    network_subparsers = network_parser.add_subparsers(dest="network_action")
    
    network_subparsers.add_parser("peers", help="Get connected peers")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = ShadowLedgerCLI(args.api_url)
    
    # Execute commands
    if args.command == "wallet":
        if args.wallet_action == "create":
            cli.create_wallet()
        elif args.wallet_action == "recover":
            cli.recover_wallet(args.mnemonic)
        elif args.wallet_action == "balance":
            cli.get_balance(args.address)
    
    elif args.command == "tx":
        if args.tx_action == "send":
            cli.send_transaction(args.sender, args.recipient, args.amount, args.private_key)
        elif args.tx_action == "get":
            cli.get_transaction(args.txid)
    
    elif args.command == "blockchain":
        if args.blockchain_action == "info":
            cli.get_blockchain_info()
        elif args.blockchain_action == "blocks":
            cli.get_latest_blocks(args.count)
    
    elif args.command == "network":
        if args.network_action == "peers":
            cli.get_peers()

if __name__ == "__main__":
    main() 