# -*- encoding: utf-8 -*-
from __future__ import annotations

import os
import sys
import time
import logging
import traceback
from typing import Callable

sys.path.append(os.getcwd())
from src.py.template import *
from src.py.model import ModelPackage
from src.py.gparser.gblender import BlenderBackend
from src.py.gparser.gparser import GerberParser
from src.py.blenderio import IO_IN, IO_OUT, BlenderIO
from src.py import Singleton


RENDER_SAMPLES: int = 0
RENDER_ENGINE: str = "EEVEE"

"""commands = {
            "getTemplateParams": self.getTemplateParams,
            "make3DModel": self.make3DModel,
            "exitNow": self.exitNow,
            "Detach": self.Detach,
            "renderGerberLayer": self.renderGerberLayer,
            "joinLayers": self.joinLayers,
            "renderPreview": self.renderPreview,
            "buildAssembler": self.buildAssembler,
            "makeModelAssets": self.makeModelAssets,
        }"""


class Main(Singleton):

    io: BlenderIO
    io_in: IO_IN
    uri: dict = {}

    class DetachException(Exception):
        pass

    def __init__(self) -> None:
        self.io = BlenderIO()
        self.io.begin()

    def mainloop(self):
        while True:
            try:
                self.io_in = self.io.read()
                self.dispatch(self.io_in)
            except Main.DetachException:
                break
            except Exception as e:
                self.io.write(
                    IO_OUT(
                        "ERROR",
                        {
                            "trace": traceback.format_exc(),
                            "cls": e.__class__.__name__,
                        },
                    )
                )

    def dispatch(self, io_in: IO_IN) -> Any:
        self.uri[io_in.status](self, **io_in.data)

    class register:
        def __init__(self, uri: dict) -> None:
            self.uri = uri

        def __call__(self, function: Callable, name: str = None) -> None:
            if name is None:
                name = function.__name__
            self.uri[name] = function
            return self

    register = register(uri)

    @register
    def exitNow(self):
        self.io.write(IO_OUT("OK"))
        time.sleep(0.2)
        exit()

    @register
    def Detach(self):
        raise Main.DetachException()

    @register
    def buildAssembler(self, pcb: str, setup: dict, out: str) -> IO_OUT:
        Global.Import(pcb)
        _bpy_PCB = Global.getActive()
        lift_top = Object.bboxCenter(_bpy_PCB).z + _bpy_PCB.dimensions.z / 2
        for code, setup in setup.items():
            Global.Import(f'{setup["model_pkg"]}./__mod__.glb')
            bpy_obj = Global.getActive()
            bpy_obj.name = code
            Transform.rotateZ(f"{setup['rot']}deg")
            Object.MoveTo(bpy_obj, setup["cox"], setup["coy"], lift_top)
        Global.selectAll()
        Global.Export(out)
        self.io.write(IO_OUT("OK"))

    def _render(
        engine: CONST.ENGINE, samples: int, root: Object, out: str, dpi: int
    ) -> None:
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
        if engine == "EEVEE":
            # set eevee as rendering engine
            Global.eevee(samples)
        elif engine == "CYCLES":
            Global.cycles(samples)
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

    """def _photoTop(bpy_obj, out, dpi) -> None:
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
        Object.RotateTo(camera.camera, 0, 0, "180deg")
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

    def _photoBot(bpy_obj, out) -> None:
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
        Global.delete(light)"""

    @register
    def makeModelAssets(self, template_params: dict, model_path: str) -> IO_OUT:
        Global.deleteAll()
        modelpkg = ModelPackage(model_path)
        modelpkg.make(template_params, self.io.log)
        modelpkg.shot(
            self.io.render_dpi,
            self.io.render_engine,
            self.io.render_samples,
            True,
            modelpkg.top_path,
        )
        modelpkg.shot(
            self.io.render_dpi,
            self.io.render_engine,
            self.io.render_samples,
            False,
            modelpkg.bot_path,
        )
        self.io.write(IO_OUT("OK"))

    @register
    def make3DModel(self, template_pkg_path: str, template_params: dict, save_as: str):
        TemplatePackage(template_pkg_path).execute(template_params)
        Global.Export(save_as)
        self.io.write(IO_OUT("OK"))


class Gerber(Namespace):

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

    @Main.register
    def renderGerberLayer(self, layer: dict, layer_type: dict, layer_id: str):
        if layer["mode"] in Gerber.LAYER_TYPES.keys():
            layer_appearance = Gerber.LAYER_TYPES[layer["mode"]]
        else:
            layer_appearance = layer["data"]
        backend = BlenderBackend(
            layer_appearance["dark_thickness"],
            layer_appearance["clear_thickness"],
            layer_appearance["region_thickness"],
            layer_appearance["dark_material"],
            layer_appearance["clear_material"],
            layer_appearance["region_material"],
        )
        parser = GerberParser(backend)
        parser.feed(layer["path"])
        self.io.write(IO_OUT("STREAM", {"token_count": parser.TOKEN_STACK_SIZE}))
        for progress in parser:
            if progress % 17 == 0:
                self.io.write(IO_OUT("STREAM", {"tokens_done": 17}))
                state_in = self.io.read()
                if state_in.status != "CONTINUE":
                    break
        else:
            Object.join(backend.ROOT, *Global.getAll())
            if layer_type == "BOT":
                Object.ScaleBy(backend.ROOT, z=-1)
                with Edit(backend.ROOT) as edit:
                    edit.makeNormalsConsistent()
            Global.Export(f"./temp/gerber/gerber-{layer_id}.glb")
        self.io.write(IO_OUT("END"))

    @Main.register
    def joinLayers(self, top_layers: list, bot_layers: list):
        desired = 0
        for path in top_layers:
            Global.Import(path)
            bpy_obj = Global.getActive()
            Object.MoveTo(bpy_obj, z=desired)
            desired += bpy_obj.dimensions.z
        desired = 0
        for path in bot_layers:
            Global.Import(path)
            bpy_obj = Global.getActive()
            Object.MoveTo(bpy_obj, z=-desired)
            desired += bpy_obj.dimensions.z
        root = Mesh.Rectangle(0, 0, 0)
        Object.join(root, *Global.getAll())
        Global.Export(f"{os.getcwd()}/temp/gerber/merged.glb")
        self.io.write(IO_OUT("OK"))

    @Main.register
    def renderPreview(self: Main, source: str, render_file: str) -> IO_OUT:
        Global.Import(source)
        root = Global.getActive()
        self.io.write(
            IO_OUT(
                "DONE",
                {
                    "co": Main._render(
                        self.io.render_engine,
                        self.io.render_samples,
                        root,
                        render_file,
                        self.io.render_dpi,
                    )
                },
            )
        )


Main().mainloop()
