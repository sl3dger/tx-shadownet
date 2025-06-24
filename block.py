import time
import os
import json
import hashlib

BLOCKCHAIN_FILE = "blockchain.json"
DIFFICULTY = 4
REWARD = 10

class Block:
    def __init__(self, index, timestamp, previous_hash, nonce, reward, address, txs=None, hash=None):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.reward = reward
        self.address = address
        self.txs = txs or []
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self):
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'reward': self.reward,
            'address': self.address,
            'txs': self.txs
        }
        return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'reward': self.reward,
            'address': self.address,
            'txs': self.txs,
            'hash': self.hash
        }

def load_chain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return []
    with open(BLOCKCHAIN_FILE, "r") as f:
        return json.load(f)

def save_block(block):
    chain = load_chain()
    chain.append(block.to_dict())
    with open(BLOCKCHAIN_FILE, "w") as f:
        json.dump(chain, f, indent=2)

def mine_block(address, txs=None):
    # VALIDATION START
    def calculate_balance(chain, addr):
        bal = 0
        for blk in chain:
            if blk["address"] == addr:
                bal += blk["reward"]
            for tx in blk.get("txs", []):
                if tx["from"] == addr:
                    bal -= tx["amount"]
                if tx["to"] == addr:
                    bal += tx["amount"]
        return bal

    def txid(tx):
        from hashlib import sha256
        return sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()

    chain = load_chain()
    known_txids = {txid(tx) for blk in chain for tx in blk.get("txs", [])}

    if txs is None:
        # Load mempool
        if os.path.exists("mempool.json"):
            with open("mempool.json", "r") as f:
                txs = json.load(f)
            # Clear mempool
            with open("mempool.json", "w") as f:
                json.dump([], f)
        else:
            txs = []

    # Validate txs
    valid_txs = []
    temp_balances = {}

    for tx in txs:
        # TIMESTAMP VALIDATION
        now = time.time()
        if abs(now - tx.get("timestamp", now)) > 300:
            continue  # reject tx if timestamp is older/newer than 5 min

        tid = txid(tx)
        sender = tx["from"]
        amt = tx["amount"]
        if tid in known_txids:
            continue  # already exists in chain

        if sender not in temp_balances:
            temp_balances[sender] = calculate_balance(chain, sender)

        if temp_balances[sender] >= amt:
            valid_txs.append(tx)
            temp_balances[sender] -= amt
    txs = valid_txs
    # VALIDATION END

    if txs is None:
        # Load mempool
        if os.path.exists("mempool.json"):
            with open("mempool.json", "r") as f:
                txs = json.load(f)
            # Clear mempool
            with open("mempool.json", "w") as f:
                json.dump([], f)
        else:
            txs = []

    chain = load_chain()
    index = len(chain)
    previous_hash = chain[-1]["hash"] if chain else "0" * 64
    nonce = 0
    timestamp = time.time()

    while True:
        blk = Block(index, timestamp, previous_hash, nonce, REWARD, address, txs)
        if blk.hash.startswith("0" * DIFFICULTY):
            return blk
        nonce += 1

def handle_block_commands(args):
    if args.action == "mine":
        blk = mine_block(args.address)
        save_block(blk)
        print(f"✅ Block #{blk.index} mined for {blk.address[:16]}... with {len(blk.txs)} txs")
    elif args.action == "view":
        chain = load_chain()
        for blk in chain:
            print(f"🧱 Block {blk['index']} ({blk['hash'][:12]}...)")
            print(f"  Address : {blk['address'][:16]}...")
            print(f"  Reward  : {blk['reward']}")
            print(f"  TXs     : {len(blk.get('txs', []))}\n")
    elif args.action == "balance":
        addr = args.address
        chain = load_chain()
        balance = 0
        for block in chain:
            if block["address"] == addr:
                balance += block["reward"]
            for tx in block.get("txs", []):
                if tx["from"] == addr:
                    balance -= tx["amount"]
                if tx["to"] == addr:
                    balance += tx["amount"]
        print(f"💰 Balance for {addr[:16]}...: {balance} ShadowCoin")
