import socket
import json


class GeometryDash:
    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port

    def send(self, command, *args):
        message = {
            "command": command,
            "args": list(args)
        }

        with socket.create_connection(
            (self.host, self.port),
            timeout=5
        ) as sock:
            sock.sendall(
                (json.dumps(message) + "\n").encode()
            )

            return sock.recv(4096).decode().strip()

    # -------------------------
    # Game controls
    # -------------------------

    def show_message(self, text):
        return self.send("show_message", text)

    def speed(self, value):
        return self.send("speed", value)

    def restart(self):
        return self.send("restart")

    def restart_level(self):
        return self.send("restart_level")

    def kill(self):
        return self.send("kill")

    def crash(self):
        return self.send("crash")

    # -------------------------
    # Level information
    # -------------------------

    def get_level_id(self):
        response = self.send("get_level_id")

        try:
            return int(response)
        except ValueError:
            return None

    # -------------------------
    # Request queue
    # -------------------------

    def add_level_id(self, level_id, user):
        return self.send("add_level_id", level_id, user)

    def get_requested_ids(self):
        return self.send("get_requested_ids")

    def get_current_requested_id(self):
        return self.send("get_current_requested_id")

    def next_requested_id(self):
        return self.send("next_requested_id")

    def remove_current_requested_id(self):
        return self.send("remove_current_requested_id")

    def clear_queue(self):
        return self.send("clear_queue")
