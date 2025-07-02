import time
import json
import os
import logging
import threading
from typing import Optional, List, Dict
from block import Block, load_chain, save_block, DIFFICULTY, REWARD
from p2p import send_to_peer, PEERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('miner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Miner:
    def __init__(self, address: str, peers: List[str] = None):
        self.address = address
        self.peers = peers or []
        self.is_mining = False
        self.current_block = None
        self.stats = {
            'blocks_mined': 0,
            'total_hashrate': 0,
            'start_time': time.time()
        }
        
    def load_mempool(self) -> List[Dict]:
        """Load transactions from mempool"""
        if not os.path.exists("mempool.json"):
            return []
        try:
            with open("mempool.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading mempool: {e}")
            return []
    
    def clear_mempool(self):
        """Clear the mempool after successful mining"""
        try:
            with open("mempool.json", "w") as f:
                json.dump([], f)
            logger.info("Mempool cleared")
        except Exception as e:
            logger.error(f"Error clearing mempool: {e}")
    
    def validate_transactions(self, txs: List[Dict]) -> List[Dict]:
        """Validate transactions before including in block"""
        chain = load_chain()
        valid_txs = []
        
        # Track balances for validation
        balances = {}
        
        for tx in txs:
            try:
                # Basic validation
                if not all(k in tx for k in ['from', 'to', 'amount', 'signature']):
                    continue
                    
                # Check if transaction already exists in blockchain
                tx_hash = self._calculate_tx_hash(tx)
                if self._tx_exists_in_chain(chain, tx_hash):
                    continue
                
                # Check sender balance
                sender = tx['from']
                if sender not in balances:
                    balances[sender] = self._calculate_balance(chain, sender)
                
                if balances[sender] >= tx['amount']:
                    valid_txs.append(tx)
                    balances[sender] -= tx['amount']
                    
            except Exception as e:
                logger.warning(f"Invalid transaction: {e}")
                continue
                
        return valid_txs
    
    def _calculate_tx_hash(self, tx: Dict) -> str:
        """Calculate transaction hash"""
        import hashlib
        tx_copy = dict(tx)
        tx_copy.pop('signature', None)
        return hashlib.sha256(json.dumps(tx_copy, sort_keys=True).encode()).hexdigest()
    
    def _tx_exists_in_chain(self, chain: List[Dict], tx_hash: str) -> bool:
        """Check if transaction already exists in blockchain"""
        for block in chain:
            for tx in block.get('txs', []):
                if self._calculate_tx_hash(tx) == tx_hash:
                    return True
        return False
    
    def _calculate_balance(self, chain: List[Dict], address: str) -> int:
        """Calculate balance for an address"""
        balance = 0
        for block in chain:
            if block["address"] == address:
                balance += block["reward"]
            for tx in block.get("txs", []):
                if tx["from"] == address:
                    balance -= tx["amount"]
                if tx["to"] == address:
                    balance += tx["amount"]
        return balance
    
    def mine_block(self) -> Optional[Block]:
        """Mine a new block"""
        logger.info("Starting block mining...")
        
        # Load and validate transactions
        txs = self.load_mempool()
        valid_txs = self.validate_transactions(txs)
        
        logger.info(f"Loaded {len(valid_txs)} valid transactions from mempool")
        
        # Get blockchain info
        chain = load_chain()
        index = len(chain)
        previous_hash = chain[-1]["hash"] if chain else "0" * 64
        
        # Start mining
        nonce = 0
        timestamp = time.time()
        start_time = time.time()
        hashes_per_second = 0
        
        logger.info(f"Mining block #{index} with difficulty {DIFFICULTY}")
        
        while self.is_mining:
            block = Block(index, timestamp, previous_hash, nonce, REWARD, self.address, valid_txs)
            
            if block.hash.startswith("0" * DIFFICULTY):
                mining_time = time.time() - start_time
                hashes_per_second = nonce / mining_time if mining_time > 0 else 0
                
                logger.info(f"✅ Block #{index} mined successfully!")
                logger.info(f"Hash: {block.hash}")
                logger.info(f"Nonce: {nonce}")
                logger.info(f"Mining time: {mining_time:.2f}s")
                logger.info(f"Hashrate: {hashes_per_second:.2f} H/s")
                
                # Update stats
                self.stats['blocks_mined'] += 1
                self.stats['total_hashrate'] = hashes_per_second
                
                return block
            
            nonce += 1
            
            # Log progress every 10000 hashes
            if nonce % 10000 == 0:
                hashes_per_second = nonce / (time.time() - start_time)
                logger.debug(f"Nonce: {nonce}, Hashrate: {hashes_per_second:.2f} H/s")
        
        logger.info("Mining stopped")
        return None
    
    def broadcast_block(self, block: Block):
        """Broadcast new block to peers"""
        message = {
            "type": "new_block",
            "data": block.to_dict()
        }
        
        for peer in self.peers:
            try:
                send_to_peer(peer, message)
                logger.info(f"Block broadcasted to {peer}")
            except Exception as e:
                logger.error(f"Failed to broadcast to {peer}: {e}")
    
    def start_mining(self):
        """Start continuous mining"""
        self.is_mining = True
        logger.info(f"Miner started for address: {self.address[:16]}...")
        
        while self.is_mining:
            try:
                # Check if we need to sync with network first
                self._sync_with_network()
                
                # Mine a block
                block = self.mine_block()
                
                if block and self.is_mining:
                    # Save block locally
                    save_block(block)
                    
                    # Clear mempool
                    self.clear_mempool()
                    
                    # Broadcast to peers
                    self.broadcast_block(block)
                    
                    logger.info(f"Block #{block.index} successfully mined and broadcasted")
                    
            except Exception as e:
                logger.error(f"Error during mining: {e}")
                time.sleep(5)  # Wait before retrying
    
    def stop_mining(self):
        """Stop mining"""
        self.is_mining = False
        logger.info("Mining stopped")
    
    def _sync_with_network(self):
        """Sync with network to get latest blocks and transactions"""
        for peer in self.peers:
            try:
                # Get latest chain
                response = send_to_peer(peer, {"type": "get_chain"})
                if response:
                    # TODO: Implement chain validation and sync
                    pass
                    
                # Get latest mempool
                response = send_to_peer(peer, {"type": "get_mempool"})
                if response:
                    # TODO: Merge mempool transactions
                    pass
                    
            except Exception as e:
                logger.warning(f"Failed to sync with {peer}: {e}")
    
    def get_stats(self) -> Dict:
        """Get mining statistics"""
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime': uptime,
            'address': self.address,
            'is_mining': self.is_mining
        }

def run_miner(address: str, peers: List[str] = None):
    """Run the miner as a standalone service"""
    miner = Miner(address, peers)
    
    try:
        miner.start_mining()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping miner...")
        miner.stop_mining()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        miner.stop_mining()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ShadowLedger Miner")
    parser.add_argument("--address", required=True, help="Miner address")
    parser.add_argument("--peers", nargs="*", default=[], help="List of peer IPs")
    
    args = parser.parse_args()
    
    run_miner(args.address, args.peers) 