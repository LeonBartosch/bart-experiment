import socket
import threading
import json

clients = []
client_ids = {}  # Maps socket to player number
next_player_id = 1
MAX_PLAYERS = 5
MAX_LEADERBOARD = 8

leaderbord = []

def handle_client(conn, addr):
    global next_player_id
    global leaderbord

    player_id = next_player_id
    next_player_id += 1
    client_ids[conn] = player_id

    print(f"[CONNECTED] Player {player_id} joined from {addr}")
    print(f"[INFO] {len(clients)} players connected.")

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            # Decode and parse JSON
            try:
                message_obj = json.loads(data.decode())
                leaderbord.append(message_obj)
                leaderbord = sorted(leaderbord, key=lambda x: int(x["pumps"]), reverse=True)
                leaderbord = leaderbord[:MAX_LEADERBOARD]
                print(leaderbord)
                
                # Relay message to other clients
                for c in clients:
                    c.sendall(json.dumps(leaderbord).encode())
            except json.JSONDecodeError as e:
                print(f"[ERROR] Could not parse message: {e}")

    except Exception as e:
        print(f"[ERROR] Player {player_id}: {e}")
    finally:
        conn.close()
        clients.remove(conn)
        print(f"[DISCONNECTED] Player {player_id}")
        print(f"[INFO] {len(clients)} players connected.")
        del client_ids[conn]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

HOST_IP = get_local_ip()
PORT = 5555

print(f"[INFO] Server running on IP: {HOST_IP}, Port: {PORT}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", PORT))  # Accept connections on all interfaces
server.listen(MAX_PLAYERS)
print("[SERVER READY] Waiting for players...")

while True:
    if len(clients) < MAX_PLAYERS:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    else:
        print("[WARNING] Max players reached. New connection refused.")
        conn, addr = server.accept()
        conn.sendall(b"Server is full. Try again later.")
        conn.close()
