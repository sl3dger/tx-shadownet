import pytest
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1
from wallet import generate_wallet
from block import Block
import time

def test_wallet_generation():
    wallet = generate_wallet()
    assert wallet["mnemonic"]
    assert wallet["private_key"]
    assert wallet["public_key"]
    assert wallet["address"].startswith("shadow1")

def test_block_hash_consistency():
    txs = [{"from": "A", "to": "B", "amount": 5, "timestamp": time.time()}]
    blk = Block(0, time.time(), "0"*64, 42, 10, "miner123", txs)
    hash1 = blk.calculate_hash()
    hash2 = blk.calculate_hash()
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64

def test_mnemonic_validity():
    mnemo = Mnemonic("english")
    wallet = generate_wallet()
    assert mnemo.check(wallet["mnemonic"])
