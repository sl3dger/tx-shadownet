import json
import time
import os
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from mnemonic import Mnemonic
from block import load_chain

MEMPOOL_FILE = "mempool.json"

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, private_key: str):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.private_key = private_key
        self.timestamp = time.time()
        self.txid = None
        self.signature = None
        
    def sign(self):
        """Sign the transaction"""
        try:
            # Create transaction data
            tx_data = {
                "from": self.sender,
                "to": self.recipient,
                "amount": self.amount,
                "timestamp": self.timestamp
            }
            
            # Sign the transaction
            tx_string = json.dumps(tx_data, sort_keys=True)
            private_key_obj = SigningKey.from_string(bytes.fromhex(self.private_key), curve=SECP256k1)
            self.signature = private_key_obj.sign(tx_string.encode()).hex()
            
            # Generate transaction ID
            self.txid = sha256(tx_string.encode()).hexdigest()
            
            return True
        except Exception as e:
            print(f"Error signing transaction: {e}")
            return False
    
    def is_valid(self) -> bool:
        """Validate the transaction"""
        try:
            # Check if transaction is signed
            if not self.signature:
                if not self.sign():
                    return False
            
            # Verify signature
            tx_data = {
                "from": self.sender,
                "to": self.recipient,
                "amount": self.amount,
                "timestamp": self.timestamp
            }
            
            tx_string = json.dumps(tx_data, sort_keys=True)
            public_key = SigningKey.from_string(bytes.fromhex(self.private_key), curve=SECP256k1).get_verifying_key()
            pub_hex = public_key.to_string().hex()
            
            if not verify_signature(tx_data, self.signature, pub_hex):
                return False
            
            # Check sender balance
            sender_balance = get_balance(self.sender)
            if sender_balance < self.amount:
                return False
            
            return True
        except Exception as e:
            print(f"Error validating transaction: {e}")
            return False
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary"""
        return {
            "from": self.sender,
            "to": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "txid": self.txid
        }

def get_address(pub_hex):
    return "shadow1" + sha256(bytes.fromhex(pub_hex)).hexdigest()[:32]

def get_balance(address):
    chain = load_chain()
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

def verify_signature(tx, signature, pubkey_hex):
    tx_copy = dict(tx)
    tx_copy.pop("signature", None)
    tx_string = json.dumps(tx_copy, sort_keys=True).encode()
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(pubkey_hex), curve=SECP256k1)
        return vk.verify(bytes.fromhex(signature), tx_string)
    except BadSignatureError:
        return False

def handle_transaction_commands(args):
    if args.action == "send":
        to = args.to
        amount = args.amount
        mnemonic = input("Sender mnemonic: ").strip()
        mnemo = Mnemonic("english")

        if not mnemo.check(mnemonic):
            print("❌ Invalid mnemonic!")
            return

        seed = mnemo.to_seed(mnemonic)
        private_key = SigningKey.from_string(seed[:32], curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        pub_hex = public_key.to_string().hex()
        sender = get_address(pub_hex)

        balance = get_balance(sender)
        if amount > balance:
            print(f"❌ Not enough balance. You have {balance} ShadowCoin.")
            return

        tx = {
            "from": sender,
            "to": to,
            "amount": amount,
            "timestamp": time.time()
        }

        tx_string = json.dumps(tx, sort_keys=True)
        signature = private_key.sign(tx_string.encode()).hex()
        tx["signature"] = signature

        # Optional: add txid for traceability
        tx["txid"] = sha256(tx_string.encode()).hexdigest()

        if not verify_signature(tx, signature, pub_hex):
            print("❌ Signature verification failed!")
            return

        # Save to mempool
        mempool = []
        if os.path.exists(MEMPOOL_FILE):
            with open(MEMPOOL_FILE, "r") as f:
                mempool = json.load(f)
        mempool.append(tx)
        with open(MEMPOOL_FILE, "w") as f:
            json.dump(mempool, f, indent=2)

        print(f"✅ Transaction of {amount} ShadowCoin added to mempool.")
