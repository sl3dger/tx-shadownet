from mnemonic import Mnemonic
from hashlib import sha256
from ecdsa import SigningKey, SECP256k1

def get_address_from_pubkey(pubkey_hex):
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    pubkey_hash = sha256(pubkey_bytes).hexdigest()
    return "shadow1" + pubkey_hash[:32]

def handle_wallet_commands(args):
    mnemo = Mnemonic("english")

    if args.action == "new":
        mnemonic = mnemo.generate(strength=128)
        seed = mnemo.to_seed(mnemonic)
        private_key = SigningKey.from_string(seed[:32], curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        address = get_address_from_pubkey(public_key.to_string().hex())

        print("🆕 Wallet Created")
        print("Mnemonic     :", mnemonic)
        print("Address      :", address)

    elif args.action == "recover":
        mnemonic = input("Mnemonic: ").strip()
        if not mnemo.check(mnemonic):
            print("❌ Invalid mnemonic!")
            return
        seed = mnemo.to_seed(mnemonic)
        private_key = SigningKey.from_string(seed[:32], curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        address = get_address_from_pubkey(public_key.to_string().hex())

        print("✅ Wallet Recovered")
        print("Address      :", address)

    elif args.action == "keys":
        mnemonic = input("Mnemonic: ").strip()
        if not mnemo.check(mnemonic):
            print("❌ Invalid mnemonic!")
            return
        seed = mnemo.to_seed(mnemonic)
        private_key = SigningKey.from_string(seed[:32], curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        address = get_address_from_pubkey(public_key.to_string().hex())

        print("🔑 Keys and Address")
        print("Private Key  :", private_key.to_string().hex())
        print("Public Key   :", public_key.to_string().hex())
        print("Address      :", address)
