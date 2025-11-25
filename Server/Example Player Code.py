import socket
import threading
import json
from psychopy import visual, core, event, gui

# Create a dialog to ask for the player number
dlg = gui.Dlg(title="Player Setup")
dlg.addField("Enter your player number (1-5):", choices=[1, 2, 3, 4, 5])
dlg.show()

# Get the player number from the dialog box
player_id = dlg.data[0]  # This will be a number (1-5)

# Connect to local server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("192.168.0.132", 5555))  # Replace with actual host IP on LAN

leaderbord = []

def receive_data():
    while True:
        try:
            data = client.recv(1024).decode()
            if data:
                leaderbord.clear()
                for leader in json.loads(data):
                    leaderbord.append(leader)
                print(leaderbord)
        except:
            break

threading.Thread(target=receive_data, daemon=True).start()

# Setup window
win = visual.Window([800,600])
text = visual.TextStim(win, text="")

while True:
    keys = event.getKeys()
    if "escape" in keys:
        break
    for key in keys:
        print(leaderbord)
        msg_data = {
            "player_id": player_id,
            "pumps": key
        }
        if key == "1" or key == "2" or key == "3" or key == "4" or key == "5" or key == "6" or key == "7" or key == "8" or key == "9" or key == "0":
            client.sendall(json.dumps(msg_data).encode())

    text.text = ""
    for leader in leaderbord:
        text.text += "Player: " + str(leader['player_id']) + ", Pumps: " + str(leader['pumps']) + "\n"
    if text.text == "":
        text.text = f"Player {player_id} - Waiting..."
    text.draw()
    win.flip()
    core.wait(0.01)

win.close()
client.close()
