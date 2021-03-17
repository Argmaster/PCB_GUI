
import socket
import json
import datetime
import sys
from typing import TextIO
from src.py import Singleton




class IO_OBJECT:

    status: str
    data: dict

    def json(self):
        return (
            json.dumps(
                {
                    "status": self.status,
                    "data": self.data,
                    "time": datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S.%f"),
                }
            )
            + "\n"
        )

    def __str__(self) -> str:
        return (
            self.__class__.__name__
            + " "
            + json.dumps(
                {
                    "status": self.status,
                    "data": self.data,
                    "time": datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S.%f"),
                },
                indent="  ",
            )
        )


class IO_OUT(IO_OBJECT):
    def __init__(self, status: str, data: dict = None) -> None:
        self.status = status
        self.data = data


class IO_IN(IO_OBJECT):
    status: str
    data: dict

    def __init__(self, initializer: str) -> None:
        self.status = initializer["status"]
        self.data = initializer["data"]


class BlenderIO(Singleton):

    PORT: int = 3568
    IPv4: str = "127.0.0.1"
    MODE: str = "STREAM"

    def __init__(self) -> None:
        self.stdout: TextIO = sys.stdout
        self.stdin: TextIO = sys.stdin
        self.socket: socket.socket = None
        self.socket_io: socket.socket = None
        self.python_log_in: bool = True
        self.python_log_out: bool = True
        self.log_file = open(
            f"./temp/blenderio-{datetime.datetime.now().strftime('%Y.%m.%d-%H-%M-%S-%f')}.log",
            "a",
        )

    def __del__(self) -> None:
        if self.socket is not None:
            self.socket.close()
        if self.socket_io is not None:
            self.socket_io.close()

    def log(self, *args) -> None:
        self.log_file.write(" ".join(str(a) for a in args) + "\n")
        self.log_file.flush()

    def begin(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.socket.bind((self.IPv4, self.PORT))
                break
            except Exception:
                self.PORT += 1
                continue
        self.socket.listen()
        self.write(IO_OUT("READY", {"port": self.PORT}))
        self.MODE = "SOCKET"
        self.socket_io, address = self.socket.accept()
        mess = self.read()
        if mess.status != "READY SOCKET":
            raise Exception()
        self.python_log_in = mess.data["python_log_in"]
        self.python_log_out = mess.data["python_log_out"]
        self.render_dpi = mess.data["render_dpi"]
        global RENDER_ENGINE
        global RENDER_SAMPLES
        RENDER_ENGINE = mess.data["render_engine"]
        RENDER_SAMPLES = mess.data["render_samples"]
        self.write(IO_OUT("WAITING SOCKET"))

    def _write_stream(self, message: IO_OUT) -> None:
        self.stdout.flush()
        self.stdout.write(message.json())
        self.stdout.flush()

    def _write_socket(self, message: IO_OUT) -> None:
        self.socket_io.sendall(message.json().encode("utf-8"))

    def write(self, message: IO_OUT) -> None:
        if self.python_log_out:
            self.log(message)
        if self.MODE == "STREAM":
            self._write_stream(message)
        elif self.MODE == "SOCKET":
            self._write_socket(message)

    def _read_steam(self) -> IO_IN:
        block = self.stdin.readline().strip()
        while not block:
            block = self.stdin.readline().strip()
        return IO_IN(json.load(block))

    def _read_socket(self) -> IO_IN:
        bytebuffer = bytearray()
        while True:
            letter = self.socket_io.recv(1)
            if letter == b"\n":
                break
            else:
                bytebuffer += letter
        bytebuffer = bytebuffer.decode("utf-8")
        return IO_IN(json.loads(bytebuffer))

    def read(self) -> IO_IN:
        if self.MODE == "STREAM":
            message = self._read_steam()
        elif self.MODE == "SOCKET":
            message = self._read_socket()
        if self.python_log_in:
            self.log(message)
        return message
