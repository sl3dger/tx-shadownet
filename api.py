from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transaction import Transaction
from stealth import generate_stealth_address
import json
import os
import uuid

app = FastAPI()

BLOCKCHAIN_FILE = "shadowledger_chain.json"
MEMPOOL_FILE = "mempool.json"

class SendRequest(BaseModel):
    sender: str
    recipient: str
    amount: float
    private_key: str

@app.get("/wallet/{address}/balance")
def get_balance(address: str):
    balance = 0
    if not os.path.exists(BLOCKCHAIN_FILE):
        return {"balance": 0.0}

    with open(BLOCKCHAIN_FILE, "r") as f:
        blockchain = json.load(f)

    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx["recipient"] == address:
                balance += tx["amount"]
            if tx["sender"] == address:
                balance -= tx["amount"]

    return {"balance": round(balance, 8)}

@app.post("/wallet/send")
def send(send_request: SendRequest):
    tx = Transaction(
        sender=send_request.sender,
        recipient=send_request.recipient,
        amount=send_request.amount,
        private_key=send_request.private_key,
    )
    if not tx.is_valid():
        raise HTTPException(status_code=400, detail="Invalid transaction")

    if not os.path.exists(MEMPOOL_FILE):
        mempool = []
    else:
        with open(MEMPOOL_FILE, "r") as f:
            mempool = json.load(f)

    mempool.append(tx.to_dict())

    with open(MEMPOOL_FILE, "w") as f:
        json.dump(mempool, f, indent=2)

    return {"status": "Transaction added to mempool", "txid": tx.txid}

@app.get("/transaction/{txid}")
def get_transaction(txid: str):
    if not os.path.exists(BLOCKCHAIN_FILE):
        raise HTTPException(status_code=404, detail="Transaction not found")

    with open(BLOCKCHAIN_FILE, "r") as f:
        blockchain = json.load(f)

    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("txid") == txid:
                return tx

    raise HTTPException(status_code=404, detail="Transaction not found")
