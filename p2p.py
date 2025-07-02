import socket
import threading
import json
import time
import os
import logging
from typing import Set, List, Dict, Optional
from block import load_chain, save_block

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('p2p.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PEER_PORT = 8888
PEERS: Set[str] = set()
BLOCKCHAIN_FILE = "blockchain.json"
MEMPOOL_FILE = "mempool.json"

# Bootstrap nodes - these should be known, stable nodes
BOOTSTRAP_NODES = [
    "127.0.0.1",  # Local development
    # Add production bootstrap nodes here
]

class P2PNode:
    def __init__(self, port: int = PEER_PORT, bootstrap_nodes: List[str] = None):
        self.port = port
        self.bootstrap_nodes = bootstrap_nodes or BOOTSTRAP_NODES
        self.peers = set()
        self.is_running = False
        self.server_socket = None
        
    def start(self):
        """Start the P2P node"""
        self.is_running = True
        
        # Start server thread
        server_thread = threading.Thread(target=self._start_server, daemon=True)
        server_thread.start()
        
        # Start health check thread
        health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        health_thread.start()
        
        # Bootstrap with known nodes
        self._bootstrap()
        
        logger.info(f"P2P node started on port {self.port}")
        
    def stop(self):
        """Stop the P2P node"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("P2P node stopped")
        
    def _start_server(self):
        """Start the P2P server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(10)
            
            logger.info(f"P2P server listening on port {self.port}")
            
            while self.is_running:
                try:
                    conn, addr = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_peer, 
                        args=(conn, addr[0]), 
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.is_running:
                        logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start P2P server: {e}")
            
    def _handle_peer(self, conn: socket.socket, addr: str):
        """Handle incoming peer connection"""
        logger.info(f"New peer connection from {addr}")
        
        try:
            # Add to peers list
            self.peers.add(addr)
            
            while self.is_running:
                data = conn.recv(8192)
                if not data:
                    break
                    
                try:
                    message = json.loads(data.decode())
                    response = self._process_message(message, addr)
                    
                    if response:
                        conn.send(json.dumps(response).encode())
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {addr}")
                except Exception as e:
                    logger.error(f"Error processing message from {addr}: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling peer {addr}: {e}")
        finally:
            conn.close()
            self.peers.discard(addr)
            logger.info(f"Peer {addr} disconnected")
            
    def _process_message(self, message: Dict, addr: str) -> Optional[Dict]:
        """Process incoming P2P message"""
        msg_type = message.get('type')
        
        logger.info(f"Processing {msg_type} from {addr}")
        
        if msg_type == "get_chain":
            chain = load_chain()
            return {"type": "chain", "data": chain}
            
        elif msg_type == "get_mempool":
            mempool = self._load_mempool()
            return {"type": "mempool", "data": mempool}
            
        elif msg_type == "new_block":
            return self._handle_new_block(message["data"])
            
        elif msg_type == "new_tx":
            return self._handle_new_transaction(message["data"])
            
        elif msg_type == "ping":
            return {"type": "pong", "timestamp": time.time()}
            
        elif msg_type == "get_peers":
            return {"type": "peers", "data": list(self.peers)}
            
        elif msg_type == "sync_request":
            return self._handle_sync_request()
            
        else:
            logger.warning(f"Unknown message type: {msg_type}")
            return None
            
    def _handle_new_block(self, block_data: Dict) -> Dict:
        """Handle new block from peer"""
        try:
            # Validate block
            if not self._validate_block(block_data):
                logger.warning("Received invalid block from peer")
                return {"type": "error", "message": "Invalid block"}
                
            # Check if we already have this block
            chain = load_chain()
            if len(chain) >= block_data['index']:
                existing_block = chain[block_data['index'] - 1]
                if existing_block['hash'] == block_data['hash']:
                    return {"type": "ok", "message": "Block already exists"}
                    
            # Save block
            save_block(block_data)
            logger.info(f"New block #{block_data['index']} saved")
            
            # Broadcast to other peers
            self._broadcast_to_peers({
                "type": "new_block",
                "data": block_data
            }, exclude_peers=set())
            
            return {"type": "ok", "message": "Block accepted"}
            
        except Exception as e:
            logger.error(f"Error handling new block: {e}")
            return {"type": "error", "message": str(e)}
            
    def _handle_new_transaction(self, tx_data: Dict) -> Dict:
        """Handle new transaction from peer"""
        try:
            # Validate transaction
            if not self._validate_transaction(tx_data):
                logger.warning("Received invalid transaction from peer")
                return {"type": "error", "message": "Invalid transaction"}
                
            # Add to mempool
            mempool = self._load_mempool()
            
            # Check for duplicates
            tx_hash = self._calculate_tx_hash(tx_data)
            for tx in mempool:
                if self._calculate_tx_hash(tx) == tx_hash:
                    return {"type": "ok", "message": "Transaction already in mempool"}
                    
            mempool.append(tx_data)
            self._save_mempool(mempool)
            
            logger.info(f"New transaction added to mempool")
            
            # Broadcast to other peers
            self._broadcast_to_peers({
                "type": "new_tx",
                "data": tx_data
            }, exclude_peers=set())
            
            return {"type": "ok", "message": "Transaction accepted"}
            
        except Exception as e:
            logger.error(f"Error handling new transaction: {e}")
            return {"type": "error", "message": str(e)}
            
    def _handle_sync_request(self) -> Dict:
        """Handle blockchain sync request"""
        try:
            chain = load_chain()
            mempool = self._load_mempool()
            
            return {
                "type": "sync_response",
                "data": {
                    "chain": chain,
                    "mempool": mempool,
                    "peers": list(self.peers)
                }
            }
        except Exception as e:
            logger.error(f"Error handling sync request: {e}")
            return {"type": "error", "message": str(e)}
            
    def _validate_block(self, block: Dict) -> bool:
        """Validate block structure and hash"""
        try:
            required_fields = ['index', 'timestamp', 'previous_hash', 'nonce', 'reward', 'address', 'hash']
            if not all(field in block for field in required_fields):
                return False
                
            # Basic hash validation
            if not block['hash'].startswith('0' * 4):  # DIFFICULTY
                return False
                
            return True
        except Exception:
            return False
            
    def _validate_transaction(self, tx: Dict) -> bool:
        """Validate transaction structure"""
        try:
            required_fields = ['from', 'to', 'amount', 'signature']
            if not all(field in tx for field in required_fields):
                return False
                
            # Basic amount validation
            if tx['amount'] <= 0:
                return False
                
            return True
        except Exception:
            return False
            
    def _calculate_tx_hash(self, tx: Dict) -> str:
        """Calculate transaction hash"""
        import hashlib
        tx_copy = dict(tx)
        tx_copy.pop('signature', None)
        return hashlib.sha256(json.dumps(tx_copy, sort_keys=True).encode()).hexdigest()
        
    def _load_mempool(self) -> List[Dict]:
        """Load mempool from file"""
        if not os.path.exists(MEMPOOL_FILE):
            return []
        try:
            with open(MEMPOOL_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading mempool: {e}")
            return []
            
    def _save_mempool(self, mempool: List[Dict]):
        """Save mempool to file"""
        try:
            with open(MEMPOOL_FILE, "w") as f:
                json.dump(mempool, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving mempool: {e}")
            
    def _bootstrap(self):
        """Bootstrap with known nodes"""
        logger.info("Bootstrapping with known nodes...")
        
        for node in self.bootstrap_nodes:
            if node != "127.0.0.1":  # Don't connect to self
                try:
                    self._connect_to_peer(node)
                except Exception as e:
                    logger.warning(f"Failed to bootstrap with {node}: {e}")
                    
    def _connect_to_peer(self, ip: str):
        """Connect to a peer"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, self.port))
            
            # Send ping to verify connection
            ping_msg = {"type": "ping", "timestamp": time.time()}
            s.send(json.dumps(ping_msg).encode())
            
            response = s.recv(1024).decode()
            if response:
                response_data = json.loads(response)
                if response_data.get('type') == 'pong':
                    self.peers.add(ip)
                    logger.info(f"Successfully connected to peer {ip}")
                    
            s.close()
            
        except Exception as e:
            logger.warning(f"Failed to connect to peer {ip}: {e}")
            
    def _health_check_loop(self):
        """Periodic health check of peers"""
        while self.is_running:
            time.sleep(30)  # Check every 30 seconds
            
            dead_peers = set()
            for peer in self.peers:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((peer, self.port))
                    
                    ping_msg = {"type": "ping", "timestamp": time.time()}
                    s.send(json.dumps(ping_msg).encode())
                    
                    response = s.recv(1024).decode()
                    s.close()
                    
                    if not response:
                        dead_peers.add(peer)
                        
                except Exception:
                    dead_peers.add(peer)
                    
            # Remove dead peers
            for peer in dead_peers:
                self.peers.discard(peer)
                logger.info(f"Removed dead peer: {peer}")
                
    def _broadcast_to_peers(self, message: Dict, exclude_peers: Set[str] = None):
        """Broadcast message to all peers except excluded ones"""
        exclude_peers = exclude_peers or set()
        
        for peer in self.peers - exclude_peers:
            try:
                self._send_to_peer(peer, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {peer}: {e}")
                
    def _send_to_peer(self, ip: str, message: Dict):
        """Send message to specific peer"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, self.port))
            s.send(json.dumps(message).encode())
            s.close()
        except Exception as e:
            logger.error(f"Failed to send to {ip}: {e}")
            
    def sync_with_network(self):
        """Sync blockchain with network"""
        logger.info("Syncing with network...")
        
        for peer in self.peers:
            try:
                response = self._send_sync_request(peer)
                if response and response.get('type') == 'sync_response':
                    data = response['data']
                    
                    # Update blockchain if peer has longer chain
                    if len(data['chain']) > len(load_chain()):
                        # TODO: Implement proper chain validation and replacement
                        logger.info(f"Peer {peer} has longer chain: {len(data['chain'])} blocks")
                        
                    # Merge mempool
                    self._merge_mempool(data['mempool'])
                    
                    # Add new peers
                    for new_peer in data['peers']:
                        if new_peer not in self.peers:
                            self.peers.add(new_peer)
                            
            except Exception as e:
                logger.warning(f"Failed to sync with {peer}: {e}")
                
    def _send_sync_request(self, ip: str) -> Optional[Dict]:
        """Send sync request to peer"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ip, self.port))
            
            sync_msg = {"type": "sync_request"}
            s.send(json.dumps(sync_msg).encode())
            
            response = s.recv(8192).decode()
            s.close()
            
            if response:
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Failed to send sync request to {ip}: {e}")
            
        return None
        
    def _merge_mempool(self, peer_mempool: List[Dict]):
        """Merge peer mempool with local mempool"""
        local_mempool = self._load_mempool()
        
        # Create set of existing transaction hashes
        existing_hashes = {self._calculate_tx_hash(tx) for tx in local_mempool}
        
        # Add new transactions
        for tx in peer_mempool:
            tx_hash = self._calculate_tx_hash(tx)
            if tx_hash not in existing_hashes:
                local_mempool.append(tx)
                existing_hashes.add(tx_hash)
                
        self._save_mempool(local_mempool)
        logger.info(f"Merged mempool: {len(local_mempool)} transactions")

# Global node instance
node = P2PNode()

def start_node():
    """Start the P2P node"""
    node.start()

def stop_node():
    """Stop the P2P node"""
    node.stop()

def send_to_peer(ip: str, message: Dict):
    """Send message to peer (legacy function for compatibility)"""
    return node._send_to_peer(ip, message)

def handle_peer(conn, addr):
    """Legacy function for compatibility"""
    node._handle_peer(conn, addr)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ShadowLedger P2P Node")
    parser.add_argument("--port", type=int, default=PEER_PORT, help="P2P port")
    parser.add_argument("--bootstrap", nargs="*", default=BOOTSTRAP_NODES, help="Bootstrap nodes")
    
    args = parser.parse_args()
    
    node = P2PNode(args.port, args.bootstrap)
    
    try:
        node.start()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping node...")
        node.stop()
