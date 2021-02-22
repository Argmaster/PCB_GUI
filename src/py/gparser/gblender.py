import sys, os
from math import atan, pi
from numpy.lib.function_base import iterable

sys.path.append(os.getcwd())
from .gparser import DrawingBackendAbstract, Constant
from src.py.bpyx import *


def _INtoMM(value: float or Iterable) -> float or Tuple:
    if iterable(value):
        out = []
        for sub_value in value:
            out.append(_INtoMM(sub_value))
        return tuple(out)
    else:
        return value * 25.4


def INtoMM(flag: str = "IN", *args: float):
    if flag == "IN":
        return _INtoMM(args)
    else:
        return args


class Rectangle:
    def __init__(
        self,
        x: float,
        y: float,
        holeDiameter: float,
        *_,
        backend: object,
    ) -> None:
        """
        Args:
            width (float): width of rectangle as raw co
            height (float): height of rectangle as raw co
            holeDiameter (float): diameter of hole in shape as raw co
            backend (PillowBackend): backend instance to draw with
        """
        self.BACKEND = backend
        self.X = x
        self.Y = y
        self.HR = holeDiameter / 2

    def flash(self, position, height, lift) -> BlenderObject:
        bpy_obj = Mesh.Rectangle(self.X, self.Y, height)
        Object.MoveBy(bpy_obj, position[0], position[1], lift)
        self.BACKEND.CURRENT_MATERIAL.assign(bpy_obj)
        return bpy_obj

    def line(self, begin, end, height, lift) -> BlenderObject:
        bpy_obj = Mesh.Rectangle(self.X, self.Y, height)
        Object.MoveBy(bpy_obj, begin[0], begin[1], lift)
        vd = [end[0] - begin[0], end[1] - begin[1], 0]
        with Edit(bpy_obj) as edit:
            edit.deselectAll()
            for face in edit.faces:
                fn = face.normal
                if fn[0] * vd[0] > 0 or fn[1] * vd[1] > 0:
                    face.select = True
            edit.extrude(vd[0], vd[1], 0)
        self.BACKEND.CURRENT_MATERIAL.assign(bpy_obj)
        return bpy_obj


class Circle:
    def __init__(
        self,
        diameter: float,
        holeDiameter: float,
        *_,
        backend: object,
    ) -> None:
        """
        Args:
            diameter (float): diameter of this shape as raw co
            holeDiameter (float): diameter of hole in given shape as raw co
            backend (PillowBackend): backend to draw with
        """
        self.BACKEND = backend
        self.R = diameter / 2
        self.HR = holeDiameter / 2

    def flash(self, position, height, lift) -> BlenderObject:
        diameter = self.R * 2
        bpy_obj = Mesh.Circle(diameter, diameter, height, vertices=18)
        Object.MoveBy(bpy_obj, position[0], position[1], lift)
        self.BACKEND.CURRENT_MATERIAL.assign(bpy_obj)
        return bpy_obj

    def line(self, begin, end, height, lift) -> BlenderObject:
        vbe = [end[0] - begin[0], end[1] - begin[1]]
        len_vbe = (vbe[0] ** 2 + vbe[1] ** 2) ** 0.5
        if vbe[0] != 0:
            alpha = atan(vbe[1] / vbe[0])
            if vbe[0] < 0:
                alpha += pi
        else:
            if vbe[1] > 0:
                alpha = pi / 2
            else:
                alpha = -pi / 2
        # Rounded edge #1 (left)
        left_half = LowLevel.makeArc(self.R, "90deg", "270deg", vertices=16)
        # Rounded edge #2 (right)
        right_half = LowLevel.makeArc(self.R, "-90deg", "90deg", vertices=16)
        Object.MoveBy(right_half, len_vbe)
        # select and join object at left-most edge
        Global.deselectAll()
        Global.select(left_half)
        Global.select(right_half)
        Global.setActive(left_half)
        Object.join(left_half, right_half)
        # create face in between two rounded edges
        with Edit(Global.getActive()) as edit:
            edit.selectAll()
            edit.makeEdgeFace()
            edit.extrude(0, 0, height)
        self.BACKEND.CURRENT_MATERIAL.assign(
            left_half,
        )
        Object.RotateBy(left_half, z=alpha)
        Object.MoveBy(left_half, begin[0], begin[1], lift)
        return left_half


class BlenderBackend(DrawingBackendAbstract):

    TOOL_TYPES = {Constant.BRUSH_RECTANGLE: Rectangle, Constant.BRUSH_CIRCLE: Circle}

    def __init__(
        self,
        DARK_Z: TType.UnitOfLength=0.10,
        CLEAR_Z: TType.UnitOfLength=0.05,
        REGION_Z: TType.UnitOfLength=0.10,
        CLEAR_MATERIAL=None,
        DARK_MATERIAL=None,
        REGION_MATERIAL=None,
        DRAW_REGION=True,
    ) -> None:
        self.TOOLS = {}
        self.REGION_VERTICES = []
        self.DARK_Z = TType.UnitOfLength.parse(DARK_Z)
        self.CLEAR_Z = TType.UnitOfLength.parse(CLEAR_Z)
        self.REGION_Z = TType.UnitOfLength.parse(REGION_Z)
        self.DRAW_REGION = DRAW_REGION
        if DARK_MATERIAL is None:
            DARK_MATERIAL = {}
        self.DARK_MATERIAL = Material().update(**DARK_MATERIAL)
        if CLEAR_MATERIAL is None:
            CLEAR_MATERIAL = {}
        self.CLEAR_MATERIAL = Material().update(**CLEAR_MATERIAL)
        if REGION_MATERIAL is None:
            REGION_MATERIAL = {}
        self.REGION_MATERIAL = Material().update(**REGION_MATERIAL)
        self.setDark()
        self.ROOT = Mesh.Rectangle(0, 0)

    def setDark(self) -> None:
        self.CURRENT_Z = self.DARK_Z
        self.CURRENT_MATERIAL = self.DARK_MATERIAL

    def setClear(self) -> None:
        self.CURRENT_Z = self.CLEAR_Z
        self.CURRENT_MATERIAL = self.CLEAR_MATERIAL

    def setSize(
        self,
        width: float,
        height: float,
        originOffsetX: float,
        originOffsetY: float,
    ):
        width, height, originOffsetX, originOffsetY = INtoMM(
            self.PARSER.UNIT, width, height, originOffsetX, originOffsetY
        )
        self.width = width
        self.height = height
        self.originOffsetX = originOffsetX
        self.originOffsetY = originOffsetY

    def drawFlash(
        self,
        position: Tuple[float, float],
        brushID: str,
    ) -> None:
        self.TOOLS[brushID].flash(
            *INtoMM(self.PARSER.UNIT, position), self.CURRENT_Z, self.REGION_Z
        )

    def drawLine(
        self,
        begin: tuple,
        end: tuple,
        brushID: str,
        isRegion: bool,
    ) -> None:
        begin, end = INtoMM(self.PARSER.UNIT, begin, end)
        if not isRegion:
            self.TOOLS[brushID].line(begin, end, self.CURRENT_Z, self.REGION_Z)
        else:
            self.REGION_VERTICES.append((end[0], end[1], 0))

    def drawArc(
        self,
        begin: tuple,
        end: tuple,
        origin: tuple,
        quadrant: Constant,
        rotation_direction: Constant,
        brushID: str,
        isRegion: bool,
    ) -> None:
        begin, end, origin = INtoMM(self.PARSER.UNIT, begin, end, origin)

    def addTool(
        self,
        identifier: str,
        brushType: str,
        params: list,
    ) -> None:
        self.TOOLS[identifier] = self.TOOL_TYPES[brushType](
            *INtoMM(self.PARSER.UNIT, *params), backend=self
        )

    def finishRegion(
        self,
    ) -> None:
        if self.DRAW_REGION:
            obj = LowLevel.fromPyData(
                self.REGION_VERTICES,
                [(index, index + 1) for index in range(len(self.REGION_VERTICES) - 1)],
            )
            self.REGION_VERTICES.clear()
            with Edit(obj) as edit:
                edit.makeEdgeFace()
                edit.extrude(0, 0, self.REGION_Z)
            self.REGION_MATERIAL.assign(obj)

    def end(self) -> None:
        Global.selectAll()
        Global.setActive(self.ROOT)
        Object.join(Global.getActive(), *Global.getSelected())
        with Edit(self.ROOT) as edit:
            edit.removeDoubles()
