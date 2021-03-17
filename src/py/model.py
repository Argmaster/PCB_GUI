# -*- encoding: utf-8 -*-
import json
import os
from typing import Callable
from py.bpyx import *
from src.py.template import TemplatePackage



class ModelPackage:
    def __init__(self, package_path: str) -> None:
        self.package_path = package_path
        self.dec_path = f"{package_path}/__dec__.json"
        self.bot_path = f"{package_path}/__bot__.png"
        self.top_path = f"{package_path}/__top__.png"
        self.ico_path = f"{package_path}/__ico__.png"
        self.mod_path = f"{package_path}/__mod__.glb"
        with open(self.dec_path, "r", encoding="utf-8") as file:
            self.dec_dict = json.load(file)
        self._class = str(self.dec_dict.get("class"))
        self._model = str(self.dec_dict.get("model"))
        self._author = str(self.dec_dict.get("author"))
        self._dscp = str(self.dec_dict.get("dscp"))
        self._other = list(self.dec_dict.get("other"))
        self.prm_dict = self.dec_dict.get("prm_dict")
        self.template = TemplatePackage(f'{os.getcwd()}/data/assets/templates/{self._class}')

    def params(self):
        return self.prm_dict

    def topShot(self, engine: str, sample_count: int) -> None:
        # responsible for making top screenshot
        Global.deleteAll()
        Global.Import(self.mod_path)
        bpy_obj = Global.getActive()
        bbox = Object.bbox(bpy_obj)
        max_xy = max(bbox, key=lambda co: max(co.x, co.y, co.z))
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

    def botShot(self) -> None:
        # responsible for making bottom screenshot
        Global.deleteAll()
        Global.Import(self.mod_path)
        #Global.render(self.bot_path, ...)

    def make(self, custom_config: dict=None, log_func: Callable=lambda *_, **__: None) -> None:
        # responsible for making 3D model if template._gtype == "python"
        # otherwise raises exception
        if self.template._gtype != "python":
            raise TemplatePackage.NotPythonGtypeError()
        if custom_config is None:
            custom_config = self.prm_dict
        self.template.execute(custom_config, log_func)
        Global.Export(self.mod_path)