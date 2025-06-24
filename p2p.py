import socket
import threading
import json
import time
import os

PEER_PORT = 8888
PEERS = set()
BLOCKCHAIN_FILE = "blockchain.json"
MEMPOOL_FILE = "mempool.json"

def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def handle_peer(conn, addr):
    print(f"[CONNECTED] {addr}")
    try:
        data = conn.recv(8192).decode()
        if data:
            message = json.loads(data)
            print(f"[RECEIVED] {message.get('type')} from {addr}")

            if message["type"] == "get_chain":
                chain = load_json(BLOCKCHAIN_FILE)
                response = json.dumps({"type": "chain", "data": chain})
                conn.send(response.encode())

            elif message["type"] == "get_mempool":
                mempool = load_json(MEMPOOL_FILE)
                response = json.dumps({"type": "mempool", "data": mempool})
                conn.send(response.encode())

            elif message["type"] == "new_block":
                chain = load_json(BLOCKCHAIN_FILE)
                chain.append(message["data"])
                with open(BLOCKCHAIN_FILE, "w") as f:
                    json.dump(chain, f, indent=2)

            elif message["type"] == "new_tx":
                mempool = load_json(MEMPOOL_FILE)
                mempool.append(message["data"])
                with open(MEMPOOL_FILE, "w") as f:
                    json.dump(mempool, f, indent=2)

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        conn.close()

def start_node():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PEER_PORT))
    server.listen(5)
    print(f"[NODE ONLINE] Listening on port {PEER_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_peer, args=(conn, addr)).start()

def send_to_peer(ip, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, PEER_PORT))
        s.send(json.dumps(message).encode())
        response = s.recv(8192).decode()
        print(f"[RESPONSE FROM {ip}]:", response[:200])
        s.close()
    except Exception as e:
        print(f"[ERROR sending to {ip}] {e}")

if __name__ == "__main__":
    threading.Thread(target=start_node).start()
    time.sleep(1)

    # Example usage (manual trigger)
    # send_to_peer("127.0.0.1", {"type": "get_chain"})
    # send_to_peer("127.0.0.1", {"type": "new_block", "data": { ... }})
