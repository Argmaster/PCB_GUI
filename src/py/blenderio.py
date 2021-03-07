from __future__ import annotations

import json
import os
import sys
import socket
import time
import datetime
from typing import TextIO
import logging
from io import StringIO

sys.path.append(os.getcwd())
from src.py.loader import *
from src.py.modelpkg import ModelPackage
from src.py.gparser.gblender import BlenderBackend
from src.py.gparser.gparser import GerberParser


RENDER_SAMPLES: int = 0
RENDER_ENGINE: str = "EEVEE"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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


class BlenderIO:

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


def makeBotIcon(io_in: IO_IN, io: BlenderIO):
    tp = TemplatePackage(io_in.data["template_path"])
    tp.makeBotIcon(
        io_in.data["template_params"],
        TType.PathExpression.resolve(io_in.data["model_path"]),
    )
    return IO_OUT("OK")


def getTemplateParams(io_in: IO_IN, io: BlenderIO):
    TemplatePackage(io_in.data["template_path"]).params_json()
    return IO_OUT("OK")


def make3DModel(io_in: IO_IN, io: BlenderIO):
    TemplatePackage(io_in.data["template_pkg_path"]).execute(
        io_in.data["template_params"]
    )
    Global.Export(io_in.data["save_as"])
    return IO_OUT("OK")


def exitNow(io_in: IO_IN, io: BlenderIO):
    io.write(IO_OUT("OK"))
    time.sleep(0.5)
    exit()


class DetachException(Exception):
    pass


def Detach(io_in: IO_IN, io: BlenderIO):
    raise DetachException()


LAYER_TYPES = {
    "COPPER": {
        "dark_thickness": "0.1m",
        "clear_thickness": "0.05m",
        "region_thickness": "0.1m",
        "dark_material": {
            "color": "rgba(0, 23, 0, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
        "clear_material": {
            "color": "rgba(0, 76, 0, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
        "region_material": {
            "color": "rgba(0, 76, 0, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
    },
    "SILK": {
        "dark_thickness": "0.05m",
        "clear_thickness": "0.02m",
        "region_thickness": "0.0m",
        "dark_material": {
            "color": "rgba(255, 255, 255, 255)",
            "roughness": 0.5,
            "specular": 0.5,
            "metallic": 0.5,
        },
        "clear_material": {
            "color": "rgba(255, 255, 255, 255)",
            "roughness": 0.5,
            "specular": 0.5,
            "metallic": 0.5,
        },
        "region_material": {
            "color": "rgba(0, 0, 0, 255)",
            "roughness": 0.5,
            "specular": 0.5,
            "metallic": 0.5,
        },
    },
    "SOLDER_MASK": {
        "dark_thickness": "0.05m",
        "clear_thickness": "0.02m",
        "region_thickness": "0.0m",
        "dark_material": {
            "color": "rgba(135, 135, 135, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
        "clear_material": {
            "color": "rgba(135, 135, 135, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
        "region_material": {
            "color": "rgba(135, 135, 135, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
    },
    "PASTE_MASK": {
        "dark_thickness": "0.05m",
        "clear_thickness": "0.02m",
        "region_thickness": "0.0m",
        "dark_material": {
            "color": "rgba(105, 105, 105, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
        "clear_material": {
            "color": "rgba(105, 105, 105, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
        "region_material": {
            "color": "rgba(105, 105, 105, 255)",
            "roughness": 1.0,
            "specular": 0,
        },
    },
}
# TODO thickness is wrong scale -> mult by 1e3

def renderGerberLayer(io_in: IO_IN, io: BlenderIO):
    io_in.data["layer"]
    if io_in.data["layer"]["mode"] in LAYER_TYPES.keys():
        layer_appearance = LAYER_TYPES[io_in.data["layer"]["mode"]]
    else:
        layer_appearance = io_in.data["layer"]["data"]
    backend = BlenderBackend(
        layer_appearance["dark_thickness"],
        layer_appearance["clear_thickness"],
        layer_appearance["region_thickness"],
        layer_appearance["dark_material"],
        layer_appearance["clear_material"],
        layer_appearance["region_material"],
    )
    parser = GerberParser(backend)
    parser.feed(io_in.data["layer"]["path"])
    io.write(IO_OUT("STREAM", {"token_count": parser.TOKEN_STACK_SIZE}))
    for progress in parser:
        if progress % 17 == 0:
            io.write(IO_OUT("STREAM", {"tokens_done": 17}))
            state_in = io.read()
            if state_in.status != "CONTINUE":
                break
    else:
        Object.join(backend.ROOT, *Global.getAll())
        if io_in.data["layer_type"] == "BOT":
            Object.ScaleBy(backend.ROOT, z=-1)
        Global.Export(f"./temp/gerber/gerber-{io_in.data['layer_id']}.glb")
    return IO_OUT("END")


def joinLayers(io_in: IO_IN, io: BlenderIO):
    desired = 0
    for path in io_in.data["top_layers"]:
        Global.Import(path)
        bpy_obj = Global.getActive()
        Object.MoveTo(bpy_obj, z=desired)
        desired += bpy_obj.dimensions.z
    desired = 0
    for path in io_in.data["bot_layers"]:
        Global.Import(path)
        bpy_obj = Global.getActive()
        Object.MoveTo(bpy_obj, z=-desired)
        desired += bpy_obj.dimensions.z
    root = Mesh.Rectangle(0, 0, 0)
    Object.join(root, *Global.getAll())
    Global.Export(f"{os.getcwd()}/temp/gerber/merged.glb")
    return IO_OUT("OK")


def renderPreview(io_in: IO_IN, io: BlenderIO):
    Global.Import(io_in.data["source"])
    root = Global.getActive()
    # prepare to make a render
    width = root.dimensions.x
    height = root.dimensions.y
    depth = root.dimensions.z
    # relocate PCB to no intersect with camera
    Object.MoveTo(root, -width / 2, -height / 2, -depth)
    # add light source
    bpy.ops.object.light_add(
        type="SUN", align="WORLD", location=(0, 0, 0), scale=(1, 1, 1)
    )
    # add camera
    camera = Camera(location=(0, 0, root.location.z + root.dimensions.z + 1))
    camera.ortho_scale = max(width, height)
    camera.type = "ORTHO"
    camera.setMain()
    if RENDER_ENGINE == "EEVEE":
        # set eevee as rendering engine
        Global.eevee(RENDER_SAMPLES)
    elif RENDER_ENGINE == "CYCLES":
        Global.cycles(RENDER_SAMPLES)
    # render image
    io.log(
        "W & H:",
        width,
        height,
        width * io.render_dpi * 40,
        height * io.render_dpi * 40,
    )
    w = width * io.render_dpi * 40
    h = height * io.render_dpi * 40
    if w * h > 1e8:
        raise RuntimeError("Output image is too big, lower your dpi and retry.")
    else:
        Global.render(
            io_in.data["render_file"],
            w,
            h,
        )
    return IO_OUT("OK")


def buildAssembler(io_in: IO_IN, io: BlenderIO):
    Global.Import(io_in.data["pcb"])
    _bpy_PCB = Global.getActive()
    for code, setup in io_in.data["setup"].items():
        Global.Import(setup["path"])
        bpy_obj = Global.getActive()
        Object.MoveTo(bpy_obj, setup["cox"], setup["coy"], 0)
        Object.RotateTo(bpy_obj, z=TType.Angle.parse(f"{setup['rot']}deg"))
    Global.selectAll()
    Global.Export(io_in.data["out"])
    return IO_OUT("OK")


def mainloop():
    io = BlenderIO()
    io.begin()
    commands = {
        "makeBotIcon": makeBotIcon,
        "getTemplateParams": getTemplateParams,
        "make3DModel": make3DModel,
        "exitNow": exitNow,
        "Detach": Detach,
        "renderGerberLayer": renderGerberLayer,
        "joinLayers": joinLayers,
        "renderPreview": renderPreview,
        "buildAssembler": buildAssembler,
    }
    while True:
        try:
            io_in = io.read()
            io.log(io_in)
            io_out = commands[io_in.status](io_in, io)
            io.write(io_out)
        except DetachException:
            break
        except Exception as e:
            error_message = StringIO()
            logging.basicConfig(stream=error_message)
            logging.exception(e)
            io.write(
                IO_OUT(
                    "ERROR",
                    {"trace": error_message.getvalue(), "cls": e.__class__.__name__},
                )
            )


mainloop()
