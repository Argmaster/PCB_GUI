# -*- encoding: utf-8 -*-
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
        "dark_thickness": "0.4mm",
        "clear_thickness": "0.2mm",
        "region_thickness": "1mm",
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
        "dark_thickness": "0.05mm",
        "clear_thickness": "0.02mm",
        "region_thickness": "0",
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
        "dark_thickness": "0.05mm",
        "clear_thickness": "0.02mm",
        "region_thickness": "0",
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
        "dark_thickness": "0.05mm",
        "clear_thickness": "0.02mm",
        "region_thickness": "0",
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
            with Edit(backend.ROOT) as edit:
                edit.makeNormalsConsistent()
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


def _render(root: Object, out: str, dpi: int):
    # prepare to make a render
    width = root.dimensions.x
    height = root.dimensions.y
    center = Object.bboxCenter(root)
    # add light source
    bpy.ops.object.light_add(type="SUN")
    light = Global.getActive()
    Object.RotateTo(light, 0, 0, 0)
    # add camera
    camera = Camera()
    Object.MoveTo(
        camera.camera,
        center.x,
        center.y,
        root.location.z + root.dimensions.z + 1,
    )
    camera.ortho_scale = max(width, height)
    camera.type = "ORTHO"
    camera.setMain()
    if RENDER_ENGINE == "EEVEE":
        # set eevee as rendering engine
        Global.eevee(RENDER_SAMPLES)
    elif RENDER_ENGINE == "CYCLES":
        Global.cycles(RENDER_SAMPLES)
    # render image
    w = width * dpi * 40
    h = height * dpi * 40
    if w * h > 1e8:
        raise RuntimeError("Output image is too big, lower your dpi and retry.")
    else:
        if os.path.exists(out):
            os.remove(out)
        Global.render(
            out,
            w,
            h,
        )
    Global.delete(camera.camera)
    Global.delete(light)
    return {
        "bx": center.x - root.dimensions.x / 2,
        "by": center.y - root.dimensions.y / 2,
        "sx": root.dimensions.x,
        "sy": root.dimensions.y,
    }


def renderPreview(io_in: IO_IN, io: BlenderIO):
    Global.Import(io_in.data["source"])
    root = Global.getActive()
    return IO_OUT("OK", {"co": _render(root, io_in.data["render_file"], io.render_dpi)})


def buildAssembler(io_in: IO_IN, io: BlenderIO):
    Global.Import(io_in.data["pcb"])
    _bpy_PCB = Global.getActive()
    lift_top = Object.bboxCenter(_bpy_PCB).z + _bpy_PCB.dimensions.z / 2
    for code, setup in io_in.data["setup"].items():
        Global.Import(f'{setup["model_pkg"]}./__mod__.glb')
        bpy_obj = Global.getActive()
        bpy_obj.name = code
        Object.MoveTo(bpy_obj, setup["cox"], setup["coy"], lift_top)
        Object.RotateTo(bpy_obj, z=TType.Angle.parse(f"{setup['rot']}deg"))
    Global.selectAll()
    Global.Export(io_in.data["out"])
    return IO_OUT("OK")


def _photoTop(bpy_obj, out, dpi):
    width = bpy_obj.dimensions.x
    height = bpy_obj.dimensions.y
    bbox = Object.bbox(bpy_obj)
    max_xy = 0
    for co in bbox:
        if abs(co.x) > max_xy:
            max_xy = abs(co.x)
        if abs(co.y) > max_xy:
            max_xy = abs(co.y)
    bpy.ops.object.light_add(type="SUN")
    light = Global.getActive()
    Object.RotateTo(light, 0, 0, 0)
    camera = Camera()
    Object.MoveTo(
        camera.camera,
        bpy_obj.location.x,
        bpy_obj.location.y,
        bpy_obj.location.z + bpy_obj.dimensions.z + 1,
    )
    camera.ortho_scale = max_xy * 2
    camera.type = "ORTHO"
    camera.setMain()
    if RENDER_ENGINE == "EEVEE":
        # set eevee as rendering engine
        Global.eevee(RENDER_SAMPLES)
    elif RENDER_ENGINE == "CYCLES":
        Global.cycles(RENDER_SAMPLES)
    max_xy = max_xy * dpi * 40 * 2
    if max_xy ** 2 > 1e8:
        raise RuntimeError("Output image is too big, lower your dpi and retry.")
    else:
        if os.path.exists(out):
            os.remove(out)
        Global.render(out, max_xy, max_xy)
    Global.delete(camera.camera)
    Global.delete(light)


def _photoBot(bpy_obj, out):
    # get current object dimensions
    x, y, _ = bpy_obj.dimensions
    # scale it up to be 1
    max_dim = max(x, y)
    _s = 1 / max_dim
    Object.ScaleBy(bpy_obj, _s, _s, _s)
    bbox = Object.bbox(bpy_obj)
    max_xy = 0
    for co in bbox:
        if abs(co.x) > max_xy:
            max_xy = abs(co.x)
        if abs(co.y) > max_xy:
            max_xy = abs(co.y)
    bpy.ops.object.light_add(type="SUN")
    light = Global.getActive()
    Object.RotateTo(light, x=0, y="180deg", z=0)
    camera = Camera()
    Object.ScaleBy(camera.camera, z=-1)
    Object.MoveTo(
        camera.camera,
        bpy_obj.location.x,
        bpy_obj.location.y,
        -(bpy_obj.location.z + bpy_obj.dimensions.z + 1),
    )
    camera.ortho_scale = max_xy * 2.2
    camera.type = "ORTHO"
    camera.setMain()
    if RENDER_ENGINE == "EEVEE":
        # set eevee as rendering engine
        Global.eevee(RENDER_SAMPLES)
    elif RENDER_ENGINE == "CYCLES":
        Global.cycles(RENDER_SAMPLES)
    if os.path.exists(out):
        os.remove(out)
    Global.render(out, 512, 512)
    Global.delete(camera.camera)
    Global.delete(light)


def makeModelAssets(io_in: IO_IN, io: BlenderIO):
    Global.deleteAll()
    tp = TemplatePackage(io_in.data["template_path"])
    bpy_obj = tp.execute(io_in.data["template_params"], io.log)
    Global.Export(f'{io_in.data["model_path"]}/__mod__.glb')
    _photoTop(bpy_obj, f'{io_in.data["model_path"]}/__top__.png', io.render_dpi)
    _photoBot(bpy_obj, f"{io_in.data['model_path']}/__bot__.png")
    return IO_OUT("OK")


def mainloop():
    io = BlenderIO()
    io.begin()
    commands = {
        "getTemplateParams": getTemplateParams,
        "make3DModel": make3DModel,
        "exitNow": exitNow,
        "Detach": Detach,
        "renderGerberLayer": renderGerberLayer,
        "joinLayers": joinLayers,
        "renderPreview": renderPreview,
        "buildAssembler": buildAssembler,
        "makeModelAssets": makeModelAssets,
    }
    while True:
        try:
            io_in = io.read()
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
