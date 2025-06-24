import argparse
from block import handle_block_commands
from wallet import handle_wallet_commands
from transaction import handle_transaction_commands

def main():
    parser = argparse.ArgumentParser(description="ShadowLedger CLI")
    subparsers = parser.add_subparsers(dest="module")

    # Block module
    block_parser = subparsers.add_parser("block", help="Rudarenje i prikaz blokova")
    block_sub = block_parser.add_subparsers(dest="action")
    block_sub.add_parser("mine", help="Rudarenje bloka").add_argument("--address", required=True, help="Stealth adresa rudara")
    block_sub.add_parser("view", help="Prikaz svih blokova")
    block_sub.add_parser("balance", help="Prikaz balansa").add_argument("--address", required=True)

    # Wallet module
    wallet_parser = subparsers.add_parser("wallet", help="Upravljanje walletom")
    wallet_sub = wallet_parser.add_subparsers(dest="action")
    wallet_sub.add_parser("new", help="Novi wallet")
    wallet_sub.add_parser("recover", help="Recovery iz mnemonica")
    wallet_sub.add_parser("keys", help="Prikaz ključeva i adrese")

    # Transaction module
    tx_parser = subparsers.add_parser("transaction", help="Transakcije")
    tx_sub = tx_parser.add_subparsers(dest="action")
    send = tx_sub.add_parser("send", help="Pošalji ShadowCoin")
    send.add_argument("--to", required=True, help="Stealth adresa primatelja")
    send.add_argument("--amount", required=True, type=int, help="Količina za slanje")

    args = parser.parse_args()

    if args.module == "block":
        handle_block_commands(args)
    elif args.module == "wallet":
        handle_wallet_commands(args)
    elif args.module == "transaction":
        handle_transaction_commands(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
