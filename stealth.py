import os
import hashlib
from ecdsa import SECP256k1, SigningKey
from mnemonic import Mnemonic

def generate_stealth_address(pub_scan_hex, pub_spend_hex):
    return "stealth1" + hashlib.sha256((pub_scan_hex + pub_spend_hex).encode()).hexdigest()[:32]

def derive_shared_key(pub_scan, priv_spend):
    shared = priv_spend.privkey.secret_multiplier * pub_scan.pubkey.point
    shared_bytes = int(shared.x()).to_bytes(32, 'big')
    return hashlib.sha256(shared_bytes).digest()

def generate_stealth_keys(mnemonic_phrase):
    mnemo = Mnemonic("english")
    if not mnemo.check(mnemonic_phrase):
        raise ValueError("Invalid mnemonic")

    seed = mnemo.to_seed(mnemonic_phrase)
    priv_scan = SigningKey.from_string(seed[:32], curve=SECP256k1)
    priv_spend = SigningKey.from_string(seed[32:64], curve=SECP256k1)

    pub_scan = priv_scan.get_verifying_key()
    pub_spend = priv_spend.get_verifying_key()

    pub_scan_hex = pub_scan.to_string().hex()
    pub_spend_hex = pub_spend.to_string().hex()

    stealth_addr = generate_stealth_address(pub_scan_hex, pub_spend_hex)

    return {
        "stealth_address": stealth_addr,
        "priv_scan": priv_scan.to_string().hex(),
        "priv_spend": priv_spend.to_string().hex(),
        "pub_scan": pub_scan_hex,
        "pub_spend": pub_spend_hex
    }
