from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import json
import os
import uuid
import time
import logging
from typing import List, Dict, Optional
from transaction import Transaction, get_balance, verify_signature
from stealth import generate_stealth_keys
from block import load_chain
from p2p import node

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ShadowLedger API",
    description="Production-ready API for ShadowLedger blockchain",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] if req_time > minute_ago]
        else:
            self.requests[client_ip] = []
        
        # Check if limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True

rate_limiter = RateLimiter()

# Request models with validation
class SendRequest(BaseModel):
    sender: str
    recipient: str
    amount: float
    private_key: str
    
    @validator('sender')
    def validate_sender(cls, v):
        if not v.startswith('shadow1'):
            raise ValueError('Invalid sender address format')
        return v
    
    @validator('recipient')
    def validate_recipient(cls, v):
        if not v.startswith('shadow1'):
            raise ValueError('Invalid recipient address format')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > 1000000:  # Reasonable upper limit
            raise ValueError('Amount too large')
        return v
    
    @validator('private_key')
    def validate_private_key(cls, v):
        if len(v) != 64:  # 32 bytes hex
            raise ValueError('Invalid private key length')
        try:
            int(v, 16)
        except ValueError:
            raise ValueError('Invalid private key format')
        return v

class WalletCreateRequest(BaseModel):
    pass

class WalletRecoverRequest(BaseModel):
    mnemonic: str
    
    @validator('mnemonic')
    def validate_mnemonic(cls, v):
        if len(v.split()) != 12:
            raise ValueError('Mnemonic must be 12 words')
        return v

# Middleware for rate limiting and logging
@app.middleware("http")
async def rate_limit_and_log(request: Request, call_next):
    client_ip = request.client.host
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Try again later."}
        )
    
    # Log request
    start_time = time.time()
    logger.info(f"{request.method} {request.url.path} from {client_ip}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check if blockchain file exists
        chain = load_chain()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "blockchain_length": len(chain),
            "peers_count": len(node.peers) if node else 0
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Status endpoint for monitoring
@app.get("/status")
async def get_status():
    """Get detailed system status"""
    try:
        chain = load_chain()
        
        # Calculate some statistics
        total_transactions = sum(len(block.get('txs', [])) for block in chain)
        total_rewards = sum(block.get('reward', 0) for block in chain)
        
        # Get mempool size
        mempool_size = 0
        if os.path.exists("mempool.json"):
            with open("mempool.json", "r") as f:
                mempool = json.load(f)
                mempool_size = len(mempool)
        
        return {
            "blockchain": {
                "length": len(chain),
                "total_transactions": total_transactions,
                "total_rewards": total_rewards,
                "last_block_hash": chain[-1]["hash"] if chain else None
            },
            "network": {
                "peers_count": len(node.peers) if node else 0,
                "peers": list(node.peers) if node else []
            },
            "mempool": {
                "size": mempool_size
            },
            "system": {
                "uptime": time.time() - getattr(app.state, 'start_time', time.time()),
                "version": "1.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")

# Wallet endpoints
@app.get("/wallet/{address}/balance")
async def get_balance_endpoint(address: str):
    """Get balance for a wallet address"""
    try:
        if not address.startswith('shadow1'):
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        balance = get_balance(address)
        return {"address": address, "balance": balance}
    except Exception as e:
        logger.error(f"Error getting balance for {address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get balance")

@app.post("/wallet/create")
async def create_wallet():
    """Create a new wallet"""
    try:
        from mnemonic import Mnemonic
        from ecdsa import SigningKey, SECP256k1
        
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(strength=128)
        
        # Generate stealth keys
        stealth_keys = generate_stealth_keys(mnemonic)
        
        logger.info(f"New wallet created: {stealth_keys['stealth_address'][:16]}...")
        
        return {
            "address": stealth_keys['stealth_address'],
            "mnemonic": mnemonic,
            "private_key": stealth_keys['priv_spend'],  # Use spend key as main private key
            "public_key": stealth_keys['pub_spend'],
            "stealth_keys": stealth_keys
        }
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        raise HTTPException(status_code=500, detail="Failed to create wallet")

@app.post("/wallet/recover")
async def recover_wallet(request: WalletRecoverRequest):
    """Recover wallet from mnemonic"""
    try:
        # Generate stealth keys from mnemonic
        stealth_keys = generate_stealth_keys(request.mnemonic)
        
        logger.info(f"Wallet recovered: {stealth_keys['stealth_address'][:16]}...")
        
        return {
            "address": stealth_keys['stealth_address'],
            "private_key": stealth_keys['priv_spend'],  # Use spend key as main private key
            "public_key": stealth_keys['pub_spend'],
            "stealth_keys": stealth_keys
        }
    except Exception as e:
        logger.error(f"Error recovering wallet: {e}")
        raise HTTPException(status_code=500, detail="Failed to recover wallet")

# Transaction endpoints
@app.post("/transaction/send")
async def send_transaction(request: SendRequest):
    """Send a transaction"""
    try:
        # Validate sender has sufficient balance
        sender_balance = get_balance(request.sender)
        if sender_balance < request.amount:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient balance. Available: {sender_balance}"
            )
        
        # Create transaction
        tx = Transaction(
            sender=request.sender,
            recipient=request.recipient,
            amount=request.amount,
            private_key=request.private_key,
        )
        
        if not tx.is_valid():
            raise HTTPException(status_code=400, detail="Invalid transaction")
        
        # Add to mempool
        if not os.path.exists("mempool.json"):
            mempool = []
        else:
            with open("mempool.json", "r") as f:
                mempool = json.load(f)
        
        tx_dict = tx.to_dict()
        mempool.append(tx_dict)
        
        with open("mempool.json", "w") as f:
            json.dump(mempool, f, indent=2)
        
        # Broadcast to network if P2P is available
        if node and node.peers:
            try:
                node._broadcast_to_peers({
                    "type": "new_tx",
                    "data": tx_dict
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast transaction: {e}")
        
        logger.info(f"Transaction sent: {tx.txid[:16]}... from {request.sender[:16]}... to {request.recipient[:16]}...")
        
        return {
            "status": "Transaction added to mempool",
            "txid": tx.txid,
            "amount": request.amount,
            "sender": request.sender,
            "recipient": request.recipient
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending transaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to send transaction")

@app.get("/transaction/{txid}")
async def get_transaction(txid: str):
    """Get transaction details by TXID"""
    try:
        chain = load_chain()
        
        for block in chain:
            for tx in block.get("txs", []):
                if tx.get("txid") == txid:
                    return {
                        "txid": txid,
                        "block_index": block["index"],
                        "block_hash": block["hash"],
                        "transaction": tx
                    }
        
        # Check mempool
        if os.path.exists("mempool.json"):
            with open("mempool.json", "r") as f:
                mempool = json.load(f)
            
            for tx in mempool:
                if tx.get("txid") == txid:
                    return {
                        "txid": txid,
                        "status": "pending",
                        "transaction": tx
                    }
        
        raise HTTPException(status_code=404, detail="Transaction not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction {txid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transaction")

# Blockchain endpoints
@app.get("/blockchain")
async def get_blockchain():
    """Get the entire blockchain"""
    try:
        chain = load_chain()
        return {
            "length": len(chain),
            "blocks": chain
        }
    except Exception as e:
        logger.error(f"Error getting blockchain: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blockchain")

@app.get("/blockchain/latest")
async def get_latest_block():
    """Get the latest block"""
    try:
        chain = load_chain()
        if not chain:
            raise HTTPException(status_code=404, detail="No blocks found")
        
        return chain[-1]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest block: {e}")
        raise HTTPException(status_code=500, detail="Failed to get latest block")

@app.get("/blockchain/{block_index}")
async def get_block(block_index: int):
    """Get a specific block by index"""
    try:
        chain = load_chain()
        
        if block_index < 0 or block_index >= len(chain):
            raise HTTPException(status_code=404, detail="Block not found")
        
        return chain[block_index]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting block {block_index}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get block")

# Network endpoints
@app.get("/network/peers")
async def get_peers():
    """Get list of connected peers"""
    try:
        if not node:
            return {"peers": []}
        
        return {
            "peers": list(node.peers),
            "count": len(node.peers)
        }
    except Exception as e:
        logger.error(f"Error getting peers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get peers")

@app.post("/network/sync")
async def sync_network():
    """Manually trigger network sync"""
    try:
        if not node:
            raise HTTPException(status_code=503, detail="P2P node not available")
        
        node.sync_with_network()
        return {"status": "Sync completed"}
    except Exception as e:
        logger.error(f"Error syncing network: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync network")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "path": request.url.path}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    logger.error(f"Internal server error: {exc.detail}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    app.state.start_time = time.time()
    logger.info("ShadowLedger API started")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("ShadowLedger API shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
