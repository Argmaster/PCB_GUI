# -*- encoding: utf-8 -*-
import json
import os
from typing import Callable
from src.py.bpyx import *
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
        self.template = TemplatePackage(
            f"{os.getcwd()}/data/assets/templates/{self._class}"
        )

    def params(self):
        return self.prm_dict

    def shot(
        self,
        dpi: int = 600,
        engine: CONST.ENGINE = CONST.ENGINE.EEVEE,
        sample_count: int = 32,
        top: bool = True,
        output: str = None,
        max_pixel_count: int = 1e8,
    ) -> None:
        """Method clears workspace, imports 3D model from this model package and
            renders a top or bottom view screenshot of it. Y axis is always
            oriented towards top of the image.

        Args:
            dpi (int, optional): dpi of output image. Defaults to 600.
            engine (CONST.ENGINE, optional): rendering engine. Defaults to CONST.ENGINE.EEVEE.
            sample_count (int, optional): engine rendering sample count (more = better and slower). Defaults to 32.
            top (bool, optional): True if top, bottom otherwise. Defaults to True.
            output (str, optional): output file, self.bot_path/self.top_path if None. Defaults to None.
            max_pixel_count (int, optional): Maximal count of pixels in image. Used to prevent creation of too big images. Defaults to 1e8.

        Raises:
            RuntimeError: Raised if output image exceeded pixel count limit.
        """
        # clear viewport, garbage collection is performed
        Global.deleteAll()
        # import model from self.mod_path (from package)
        bpy_obj = Global.Import(self.mod_path)
        # get bounding box of imported model
        bbox = Object.bbox(bpy_obj)
        # get max horizontal distance from (0,0,0) to bbox corner
        render_half_size = max(bbox, key=lambda co: max(abs(co.x), abs(co.y)))
        render_half_size = max(abs(render_half_size.x), abs(render_half_size.y))
        # add light to viewport, it should light up object from
        # both top and bottom due to angle="179deg"
        Light(
            CONST.LIGHT.SUN,
            rotation=(0, 0 if top else "179deg", 0),
            power=2
        )
        # create new camera either below or above object and
        # adjust rotation to face towards the object
        # camera is in ortographic mode to keep proper scale
        Camera(
            location=(
                bpy_obj.location.x,
                bpy_obj.location.y,
                (bpy_obj.location.z + bpy_obj.dimensions.z + 1)
                if top
                else -(bpy_obj.location.z + bpy_obj.dimensions.z + 1),
            ),
            rotation=(0, 0, 0) if top else (0, "180deg", 0),
            ortho_scale=render_half_size * 2.2,  # .2 for some padding around model
            type=CONST.CAM_TYPE.ORTHOGRAPHIC,  # no perspective
            main=True,  # set camera as main
        )
        if engine == CONST.ENGINE.EEVEE:
            Global.eevee(sample_count)
        elif engine == CONST.ENGINE.CYCLES:
            Global.cycles(sample_count)
        pixel_width = render_half_size * dpi * 40 * 2.2
        if pixel_width * pixel_width > max_pixel_count:
            raise RuntimeError(
                f"Output image is too big [{pixel_width}x{pixel_width}], lower your dpi and retry."
            )
        else:
            if output is None:
                output = self.top_path if top else self.bot_path
            Global.render(output, pixel_width, pixel_width)
        # clear viewport, garbage collection is performed
        Global.deleteAll()

    def make(
        self,
        custom_config: dict = None,
        log_func: Callable = lambda *_, **__: None,
    ) -> None:
        # responsible for making 3D model if template._gtype == "python"
        # otherwise raises exception
        if self.template._gtype != "python":
            raise TemplatePackage.NotPythonGtypeError()
        if custom_config is None:
            custom_config = self.prm_dict
        self.template.execute(custom_config, log_func)
        Global.Export(self.mod_path)
