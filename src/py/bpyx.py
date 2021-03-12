# -*- encoding: utf-8 -*-
from __future__ import annotations

import json
import math
import os
import sys
import time
from abc import ABC, abstractmethod
from typing import Iterable, List, Tuple, Union

sys.path.append(os.path.dirname(__file__))
from src.py.ttype import *

import bmesh
import bpy
import numpy


from mathutils import *


# $ <>=======================================================<>
# $               Global operations handler
# $ <>=======================================================<>


def log(*args, **kwargs) -> None:
    """Logging function available during execution.
    Logged text will be stremed into blender log files in
    temp folder.
    """
    pass


class Global(Namespace):
    class OperationCancelled(Exception):
        pass

    @staticmethod
    def Unique() -> str:
        """Returns hexadecimal identifer generated from current time.

        Returns:
            str: identifier.
        """
        return hex(int(time.time() * 1e5)).upper()

    @staticmethod
    def _Bpy_getActive() -> BpyObject:
        """Get currentlu active object.

        Returns:
            object: active blender object.
        """
        return bpy.context.active_object

    @staticmethod
    def _Bpy_setActive(obj: object) -> None:
        """Set currently active object

        Args:
            obj (object): blender object to be activated.
        """
        bpy.context.view_layer.objects.active = obj

    @staticmethod
    def _Bpy_deselectAll() -> None:
        """Deselect all objects that are present in viewport."""
        bpy.ops.object.select_all(action="DESELECT")

    @staticmethod
    def _Bpy_selectAll() -> None:
        """Deselect all objects that are present in viewport."""
        bpy.ops.object.select_all(action="SELECT")

    @staticmethod
    def getActive() -> BpyObject:
        """Get currentlu active object.

        Returns:
            Object: active blender object.
        """
        return Global._Bpy_getActive()

    @staticmethod
    def setActive(bpy_obj: object) -> None:
        """Set currently active object

        Args:
            bpy_obj (Object): blender object to be activated.
        """
        return Global._Bpy_setActive(bpy_obj)

    def isSelected(bpy_obj) -> bool:
        """Returns bool selection value.

        Returns:
            Bool: True if selected.
        """
        return bpy_obj.select_get()

    def select(bpy_obj) -> BpyObject:
        """Selects this object. This method do not affect
        selection of other objects.

        Returns:
            Object: bpy_obj
        """
        bpy_obj.select_set(True)
        return bpy_obj

    @staticmethod
    def selectOnly(bpy_obj) -> BpyObject:
        """Select this object and deselect all other.

        Returns:
            Object: bpy_obj
        """
        Global.deselectAll()
        Global.select(bpy_obj)
        return bpy_obj

    @staticmethod
    def deselect(bpy_obj) -> BpyObject:
        """Deselects this object. This method do not affect
        selection of other objects.

        Returns:
            Object: bpy_obj
        """
        bpy_obj.select_set(False)
        return bpy_obj

    @staticmethod
    def selectAll() -> None:
        """Select all objects that are present in viewport."""
        Global._Bpy_selectAll()

    @staticmethod
    def deselectAll() -> None:
        """Deselect all objects that are present in viewport."""
        Global._Bpy_deselectAll()

    @staticmethod
    def delete(bpy_obj: Object, garbage_collection: bool = True) -> None:
        """Removes this object, do not affects selection of other objects
        collects garbage object data.
        """
        Global.deselect(bpy_obj)
        selected = Global.getSelected()
        Global.deselectAll()
        Global.select(bpy_obj)
        bpy.ops.object.delete(use_global=False)
        for o in selected:
            Global.select(o)
        if garbage_collection:
            Global.collect_garbage()

    @staticmethod
    def deleteAll() -> None:
        """Delete all object that can be selected with selectAll method."""
        Global._Bpy_selectAll()
        bpy.ops.object.delete(use_global=False)
        Global.collect_garbage()

    @staticmethod
    def getSelected() -> list:
        """Return list of currentlu selected objects.

        Returns:
            list: active objects.
        """
        return bpy.context.selected_objects

    @staticmethod
    def getAll() -> list:
        """Returns list of all existing bpyx objects.

        Returns:
            list: list of Object
        """
        return bpy.data.objects

    @staticmethod
    def getMode() -> str:
        """Returns current working mode. Usually either EDIT_MESH or OBJECT.

        Returns:
            str: current working mode.
        """
        return bpy.context.object.mode

    @staticmethod
    def updateView() -> None:
        """Updates viewport to make changes made by script visible."""
        bpy.context.view_layer.update()

    @staticmethod
    def collect_garbage() -> None:
        for block in bpy.data.meshes:
            if block.users == 0:
                bpy.data.meshes.remove(block)

        for block in bpy.data.materials:
            if block.users == 0:
                bpy.data.materials.remove(block)

        for block in bpy.data.textures:
            if block.users == 0:
                bpy.data.textures.remove(block)

        for block in bpy.data.images:
            if block.users == 0:
                bpy.data.images.remove(block)

        for block in bpy.data.curves:
            if block.users == 0:
                bpy.data.curves.remove(block)

        for block in bpy.data.lights:
            if block.users == 0:
                bpy.data.lights.remove(block)

        for block in bpy.data.cameras:
            if block.users == 0:
                bpy.data.cameras.remove(block)

    @staticmethod
    def Import(path: str, format: str = None):
        """Import object from file in "path" location. If format is None, format will
        be definded based on file name.
        Available formats are: .obj .glb .fbx .x3d

        Args:
            path (str): path to file.
            format (str, optional): file format. Defaults to None.

        Raises:
            ValueError: raised if file format was not recognized as importable.
        """
        ext = os.path.splitext(path)[1]
        if format is None:
            format = ext
        else:
            format = f".{format.lower()}"
        if format.lower() == ".obj":
            bpy.ops.import_scene.obj(filepath=path)
        elif format.lower() == ".glb":
            bpy.ops.import_scene.gltf(filepath=path)
        elif format.lower() == ".fbx":
            bpy.ops.import_scene.fbx(filepath=path, use_selection=True)
        elif format.lower() == ".x3d":
            bpy.ops.import_scene.x3d(filepath=path, use_selection=True)
        else:
            raise ValueError(f"Unsupported file format {format}")

    @staticmethod
    def Export(path: str = "./mesh.glb", format: str = None):
        """Export whole scene (all objects) to file in "path" location. If format is None,
        format will be definded based on file name.
        Available formats are: .obj .glb .fbx .x3d

        Args:
            path (str): path to file.
            format (str, optional): file format. Defaults to None.

        Raises:
            ValueError: raised if file format was not recognized as exportable.
        """
        Global.selectAll()
        ext = os.path.splitext(path)[1]
        if format is None:
            format = ext
        else:
            format = f".{format.lower()}"
        if format.lower() == ".obj":
            bpy.ops.export_scene.obj(filepath=path, use_selection=True)
        elif format.lower() == ".glb":
            bpy.ops.export_scene.gltf(filepath=path, use_selection=True)
        elif format.lower() == ".fbx":
            bpy.ops.export_scene.fbx(filepath=path, use_selection=True)
        elif format.lower() == ".x3d":
            bpy.ops.export_scene.x3d(filepath=path, use_selection=True)
        else:
            raise ValueError(f"Unsupported file format {format}")

    @staticmethod
    def Save(path: str = "./mesh.blend"):
        bpy.ops.wm.save_as_mainfile(filepath=path)

    @staticmethod
    def eevee(render_samples: int = 64, use_high_quality_normals: bool = True):
        bpy.context.scene.render.engine = "BLENDER_EEVEE"
        eevee = bpy.context.scene.eevee
        eevee.taa_render_samples = render_samples
        bpy.context.scene.render.use_high_quality_normals = use_high_quality_normals

    @staticmethod
    def cycles(
        render_samples: int = 128,
        use_experimentals: bool = False,
        use_gpu: bool = True,
        use_adaptive_sampling: bool = False,
        use_denoising: bool = False,
        denoiser: str = "NLM",
    ):
        bpy.context.scene.render.engine = "CYCLES"
        cycles = bpy.context.scene.cycles
        cycles.samples = render_samples
        cycles.feature_set = "EXPERIMENTAL" if use_experimentals else "SUPPORTED"
        cycles.device = "GPU" if use_gpu else "CPU"
        cycles.use_adaptive_sampling = use_adaptive_sampling
        cycles.use_denoising = use_denoising
        cycles.denoiser = denoiser

    @staticmethod
    def render(
        outpath: str = "./test.png",
        resolution_x: float = 1920,
        resolution_y: float = 1080,
        tile_x: float = 64,
        tile_y: float = 64,
        threads_count: int = 0,
        film_transparent: bool = True,
    ):
        render = bpy.context.scene.render
        render.filepath = outpath
        render.resolution_x = resolution_x
        render.resolution_y = resolution_y
        render.tile_x = tile_x
        render.tile_y = tile_y
        render.film_transparent = film_transparent

        if threads_count > 0:
            render.threads_mode = "FIXED"
            render.threads = threads_count
        else:
            render.threads_mode = "AUTO"
        bpy.ops.render.render(write_still=True)


class Transform(Namespace):
    @staticmethod
    def apply(location: bool = True, rotation: bool = True, scale: bool = True):
        """Apply current transformation of object to it.

        Args:
            location (bool, optional): Flag specifying wheather to apply transform or not. Defaults to True.
            rotation (bool, optional): Flag specifying wheather to apply rotation or not. Defaults to True.
            scale (bool, optional): Flag specifying wheather to apply scale or not. Defaults to True.
        """
        bpy.ops.object.transform_apply(
            location=location, rotation=rotation, scale=scale
        )

    @staticmethod
    def transform(
        rotation: tuple = (0, 0, 0),
        translation: tuple = (0, 0, 0),
        scale: tuple = (0, 0, 0),
    ):
        """Function that can be used to transform object by vector in both Edit and Object mode.

        Args:
            rotation (tuple, optional): vector of (float, float, float). Defaults to (0, 0, 0).
            translation (tuple, optional): vector of (float, float, float). Defaults to (0, 0, 0).
            scale (tuple, optional): vector of (float, float, float). Defaults to (0, 0, 0).
        """
        Transform.scale(scale)
        Transform.rotateX(rotation[0])
        Transform.rotateY(rotation[1])
        Transform.rotateZ(rotation[2])
        Transform.translate(translation)

    @staticmethod
    def translate(
        x: TType.UnitOfLength = 0.0,
        y: TType.UnitOfLength = 0.0,
        z: TType.UnitOfLength = 0.0,
        orient_type: str = "GLOBAL",
        orient_matrix: tuple = ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type: str = "GLOBAL",
        constraint_axis: tuple = (False, False, False),
        mirror: bool = True,
        use_proportional_edit: bool = False,
        proportional_edit_falloff: str = "SMOOTH",
        proportional_size: float = 1,
        use_proportional_connected: bool = False,
        use_proportional_projected: bool = False,
        release_confirm: bool = True,
        **kwargs,
    ) -> set:
        """Apply translate transform for both object and edit mode
        Args:
            x (TType.UnitOfLength, optional): distance, parsable for TType.UnitOfLength.parse()
            y (TType.UnitOfLength, optional): distance, parsable for TType.UnitOfLength.parse()
            z (TType.UnitOfLength, optional): distance, parsable for TType.UnitOfLength.parse()
            orient_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
            orient_matrix_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
        """
        rv = bpy.ops.transform.translate(
            value=(
                TType.UnitOfLength.parse(x),
                TType.UnitOfLength.parse(y),
                TType.UnitOfLength.parse(z),
            ),
            orient_type=orient_type,
            orient_matrix=orient_matrix,
            orient_matrix_type=orient_matrix_type,
            constraint_axis=constraint_axis,
            mirror=mirror,
            use_proportional_edit=use_proportional_edit,
            proportional_edit_falloff=proportional_edit_falloff,
            proportional_size=proportional_size,
            use_proportional_connected=use_proportional_connected,
            use_proportional_projected=use_proportional_projected,
            release_confirm=release_confirm,
            **kwargs,
        )
        if not Edit.isEditMode():
            Transform.apply(True, False, False)
        return rv

    @staticmethod
    def rotate(
        value: TType.Angle = 0,
        orient_axis: str = "X",
        orient_type: str = "GLOBAL",
        orient_matrix: tuple = ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type: str = "GLOBAL",
        constraint_axis: tuple = (False, False, False),
        mirror: bool = True,
        use_proportional_edit: bool = False,
        proportional_edit_falloff: str = "SMOOTH",
        proportional_size: float = 1,
        use_proportional_connected: bool = False,
        use_proportional_projected: bool = False,
        release_confirm: bool = True,
        center_override=(0.0, 0.0, 0.0),
        **kwargs,
    ) -> set:
        """Apply rotation transform to object. It works both in Object and Edit mode.
        If center_override is None it wont be contained in end rotation so center wont be overriden.

        Args:
            value (TType.Angle, optional): Angle, parsable by TType.Angle.parse(). Defaults to 0.
            orient_axis (str, optional): Axis to rotate around. Defaults to "X".
            orient_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
            orient_matrix_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
        """
        if center_override is not None:
            kwargs["center_override"] = center_override
        rv = bpy.ops.transform.rotate(
            value=TType.Angle.parse(value),
            orient_axis=orient_axis,
            orient_type=orient_type,
            orient_matrix=orient_matrix,
            orient_matrix_type=orient_matrix_type,
            constraint_axis=constraint_axis,
            mirror=mirror,
            use_proportional_edit=use_proportional_edit,
            proportional_edit_falloff=proportional_edit_falloff,
            proportional_size=proportional_size,
            use_proportional_connected=use_proportional_connected,
            use_proportional_projected=use_proportional_projected,
            release_confirm=release_confirm,
            **kwargs,
        )
        if not Edit.isEditMode():
            Transform.apply(False, True, False)
        return rv

    @staticmethod
    def rotateX(
        value: TType.Angle, center_override: tuple = (0.0, 0.0, 0.0), **kwargs
    ) -> set:
        """Rotate currently selected object in predefined axis. It works both in Object and Edit mode.
        If center_override is None it wont be contained in end rotation so center wont be overriden.

        Args:
            value (TType.Angle): rotation value, parsable by TType.Angle.parse
            center_override (tuple, optional): Overwriting of rotation center. Defaults to (0.0, 0.0, 0.0).

        Returns:
            set: set containing operation result.
        """
        rv = Transform.rotate(
            value,
            orient_axis="X",
            constraint_axis=(True, False, False),
            center_override=center_override,
            **kwargs,
        )
        if not Edit.isEditMode():
            Transform.apply(False, True, False)
        return rv

    @staticmethod
    def rotateY(
        value: TType.Angle, center_override: tuple = (0.0, 0.0, 0.0), **kwargs
    ) -> set:
        """Rotate currently selected object in predefined axis. It works both in Object and Edit mode.
        If center_override is None it wont be contained in end rotation so center wont be overriden.

        Args:
            value (TType.Angle): rotation value, parsable by TType.Angle.parse
            center_override (tuple, optional): Overwriting of rotation center. Defaults to (0.0, 0.0, 0.0).

        Returns:
            set: set containing operation result.
        """
        rv = Transform.rotate(
            value,
            orient_axis="Y",
            constraint_axis=(False, True, False),
            center_override=center_override,
            **kwargs,
        )
        if not Edit.isEditMode():
            Transform.apply(False, True, False)
        return rv

    @staticmethod
    def rotateZ(
        value: TType.Angle, center_override: tuple = (0.0, 0.0, 0.0), **kwargs
    ) -> set:
        """Rotate currently selected object in predefined axis. It works both in Object and Edit mode.
        If center_override is None it wont be contained in end rotation so center wont be overriden.

        Args:
            value (TType.Angle): rotation value, parsable by TType.Angle.parse
            center_override (tuple, optional): Overwriting of rotation center. Defaults to (0.0, 0.0, 0.0).

        Returns:
            set: set containing operation result.
        """
        rv = Transform.rotate(
            value,
            orient_axis="Z",
            constraint_axis=(False, False, True),
            center_override=center_override,
            **kwargs,
        )
        if not Edit.isEditMode():
            Transform.apply(False, True, False)
        return rv

    @staticmethod
    def scale(
        x: float = 1.0,
        y: float = 1.0,
        z: float = 1.0,
        orient_type: str = "GLOBAL",
        orient_matrix: tuple = ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type: str = "GLOBAL",
        constraint_axis: Tuple[bool, bool, bool] = (False, False, False),
        mirror: bool = True,
        use_proportional_edit: bool = False,
        proportional_edit_falloff: str = "SMOOTH",
        proportional_size: float = 1,
        use_proportional_connected: bool = False,
        use_proportional_projected: bool = False,
        release_confirm: bool = True,
        **kwargs,
    ) -> set:
        """Scale currently selected object. It works both in object and edit mode.

        Args:
            x (float, optional): scale along x axis
            y (float, optional): scale along y axis
            z (float, optional): scale along z axis
            orient_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"]. Defaults to "GLOBAL".
            orient_matrix (tuple, optional): . Defaults to ((1, 0, 0), (0, 1, 0), (0, 0, 1)).
            orient_matrix_type (str, optional): . Defaults to "GLOBAL".
            constraint_axis (Tuple[bool, bool, bool], optional): . Defaults to (False, False, False).
            mirror (bool, optional): . Defaults to True.
            use_proportional_edit (bool, optional): . Defaults to False.
            proportional_edit_falloff (str, optional): . Defaults to "SMOOTH".
            proportional_size (float, optional): . Defaults to 1.
            use_proportional_connected (bool, optional): . Defaults to False.
            use_proportional_projected (bool, optional): . Defaults to False.
            release_confirm (bool, optional): . Defaults to True.
        """
        rv = bpy.ops.transform.resize(
            value=(x, y, z),
            orient_type=orient_type,
            orient_matrix=orient_matrix,
            orient_matrix_type=orient_matrix_type,
            constraint_axis=constraint_axis,
            mirror=mirror,
            use_proportional_edit=use_proportional_edit,
            proportional_edit_falloff=proportional_edit_falloff,
            proportional_size=proportional_size,
            use_proportional_connected=use_proportional_connected,
            use_proportional_projected=use_proportional_projected,
            release_confirm=release_confirm,
            **kwargs,
        )
        if not Edit.isEditMode():
            Transform.apply(False, False, True)
        return rv


Global.deleteAll()

# $ <>=======================================================<>
# $                   Edit mode handler
# $ <>=======================================================<>


class Edit:
    """Can be used with context manager to switch to fully featured edit mode."""

    _isEditMode: bool = False
    BMESH = None

    def __init__(self, bpy_obj: Object) -> None:
        """Edit mode is ment to be used with context manager to enter edit mode for short period of time to modify
        bpy_obj passed to constructor.

        Args:
            bpy_obj: Object to be modfied.
        """
        self.bpy_obj = bpy_obj

    @staticmethod
    def isEditMode():
        return Edit._isEditMode

    def __enter__(self) -> Edit:
        """Implements context manager enter method. Enters blender edit mode to modify editObject that
        was passed to the constructor. It also creates bmesh object to allow access to faces, edges
        and vertices currently edited mesh.

        Returns:
            object: self
        """
        self.enter()
        return self

    def enter(self) -> Edit:
        Global.setActive(self.bpy_obj)
        Global.selectOnly(self.bpy_obj)
        bpy.ops.object.mode_set(mode="EDIT")
        Edit._isEditMode = True
        self.BMESH = bmesh.from_edit_mesh(self.bpy_obj.data)
        self.selectAll()
        return self

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        """Implements context manager exit method. Leaves blender edit mode also selecting and activating
        endObject that was passed to constructor or object that was active when Edit instance was created.

        Args:
            exc_type ([type]): unknown
            exc_value ([type]): unknown
            exc_trace ([type]): unknown
        """
        self.exit()

    def exit(self):
        bpy.ops.object.mode_set(mode="OBJECT")
        Edit._isEditMode = False
        return self.bpy_obj

    @property
    def faces(self) -> Iterable:
        """Provides access to edited object bmesh attribute
        holding reference to list of all faces of edited mesh.

        Returns:
            Iterable: list of edited object faces.
        """
        self.BMESH.faces.ensure_lookup_table()
        return self.BMESH.faces

    @property
    def edges(self) -> Iterable:
        """Provides access to edited object bmesh attribute
        holding reference to list of all edges of edited mesh.

        Returns:
            Iterable: list of edited object edges.
        """
        self.BMESH.faces.ensure_lookup_table()
        return self.BMESH.edges

    @property
    def verts(self) -> Iterable:
        """Provides access to edited object bmesh attribute
        holding reference to list of all vertices of edited mesh.

        Returns:
            Iterable: list of edited object vertices.
        """
        self.BMESH.verts.ensure_lookup_table()
        return self.BMESH.verts

    @staticmethod
    def makeNormalsConsistent() -> None:
        """Shorthand for normals_make_consitent function for fixing nortmal vectors
        of currently selected faces of mesh in edit mode.
        """
        bpy.ops.mesh.normals_make_consistent(inside=False)

    @staticmethod
    def removeDoubles(treshold: float = 0.001) -> set:
        """Removes duplicated vertices from mesh

        Args:
            treshold (float, optional): distance treshold of verts to merge. Defaults to 0.001.

        Returns:
            set: result value set
        """
        return bpy.ops.mesh.remove_doubles(threshold=treshold)

    def selectVerts(
        self,
        xyz_test: callable,
    ) -> Edit:
        """Selects verices by their absolute position

        Args:
            xyz_test: (callable, optional) function returning bool selection value for co param
        """
        for v in self.verts:
            if xyz_test(v.co):
                v.select = True
        return self

    def selectEdges(
        self,
        co_test: callable,
    ) -> Edit:
        for e in self.edges:
            if co_test(e.verts[0].co, e.verts[1].co):
                e.select = True
        return self

    def selectFaces(self, facing_xyz: tuple) -> Edit:
        for face in self.faces:
            if face.normal.dot(facing_xyz) > 0:
                face.select = True

        return self

    def selectReverse(self) -> Edit:
        for v in self.verts:
            v.select = not v.select
        return self

    @staticmethod
    def selectAll() -> None:
        """Selects all faces of currently modified mesh."""
        bpy.ops.mesh.select_all(action="SELECT")

    @staticmethod
    def deselectAll() -> None:
        """Deselects all faces of currently modified mesh"""
        bpy.ops.mesh.select_all(action="DESELECT")

    @staticmethod
    def delete(type: str = "VERT"):
        """Delete currentlu selected components of edited mesh.

        Args:
            type (str, optional): Deletion mode. Defaults to "VERT".
        """
        bpy.ops.mesh.delete(type=type)

    def bevel(
        self,
        affect: str = "EDGES",
        offset_type: str = "OFFSET",
        offset: float = 0.0,
        offset_pct: float = 0.0,
        segments: int = 1,
        shape: float = 0.5,
        material_index: int = -1,
        release_confirm: bool = False,
        clamp_overlap: bool = True,
    ) -> Edit:
        """Perform bevel operation on currently selected edges

        Args:
            affect (str, optional) one of ["VERTICES", "EDGES"]
            offset_type (str, optional):
                one of ["OFFSET", "WIDTH", "DEPTH", "PERCENT", "ABSOLUTE"].
                Defaults to "OFFSET".
            offset (float, optional): Defaults to 0.0.
            offset_pct (float, optional): Defaults to 0.0.
            segments (int, optional): Defaults to 1.
            shape (float, optional): Defaults to 0.5.
            material_index (int, optional): Defaults to -1.
            release_confirm (bool, optional): Defaults to False.
        """
        if "CANCELLED" in bpy.ops.mesh.bevel(
            affect=affect,
            offset_type=offset_type,
            offset=offset,
            offset_pct=offset_pct,
            segments=segments,
            profile=shape,
            material=material_index,
            release_confirm=release_confirm,
            clamp_overlap=clamp_overlap,
        ):
            raise Global.OperationCancelled(
                f"Cancelled operation Bevel for affect: {affect}; offset_type: {offset_type}."
            )
        return self

    def extrude(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        orient_type: str = "GLOBAL",
        constraint_axis: tuple = (False, False, False),
    ) -> Edit:
        """Perform extrude operation on currently selected vertices, faces and edges of edited mesh

        Args:
            x (TType.UnitOfLength, optional): distance as float in meters or as str parsable by TType.UnitOfLength.parse
            y (TType.UnitOfLength, optional): distance as float in meters or as str parsable by TType.UnitOfLength.parse
            z (TType.UnitOfLength, optional): distance as float in meters or as str parsable by TType.UnitOfLength.parse
            orient_type (str, optional): vector orientation. Defaults to "GLOBAL".
            constraint_axis (tuple, optional): constant axis flags. Defaults to (False, False, False).

        Returns:
            self: Edit.
        """
        if "CANCELLED" in bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={
                "use_normal_flip": False,
                "use_dissolve_ortho_edges": False,
                "mirror": False,
            },
            TRANSFORM_OT_translate={
                "value": (x, y, z),
                "orient_type": orient_type,
                "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                "orient_matrix_type": "GLOBAL",
                "constraint_axis": constraint_axis,
                "mirror": False,
                "use_proportional_edit": False,
                "proportional_edit_falloff": "SMOOTH",
                "proportional_size": 1,
                "use_proportional_connected": False,
                "use_proportional_projected": False,
                "snap": False,
                "snap_target": "CLOSEST",
                "snap_point": (0, 0, 0),
                "snap_align": False,
                "snap_normal": (0, 0, 0),
                "gpencil_strokes": False,
                "cursor_transform": False,
                "texture_space": False,
                "remove_on_cancel": False,
                "release_confirm": False,
                "use_accurate": False,
                "use_automerge_and_split": False,
            },
        ):
            raise Global.OperationCancelled(
                f"Cancelled operation Extrude for xyz: {x, y, z}."
            )
        return self

    def makeEdgeFace(self) -> set:
        """Create Face connecting selected components of mesh"""
        if "CANCELLED" in bpy.ops.mesh.edge_face_add():
            raise Global.OperationCancelled(f"Cancelled operation makeEdgeFace().")

    def MoveBy(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        orient_type: str = "GLOBAL",
        **kwargs,
    ) -> Edit:
        """Move mesh relative to object root.
        Args:
            x (TType.UnitOfLength, optional): distance as float in meters or as str parsable by TType.UnitOfLength.parse
            y (TType.UnitOfLength, optional): distance as float in meters or as str parsable by TType.UnitOfLength.parse
            z (TType.UnitOfLength, optional): distance as float in meters or as str parsable by TType.UnitOfLength.parse
            orient_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
        """
        if "CANCELLED" in bpy.ops.transform.translate(
            value=(
                TType.UnitOfLength.parse(x),
                TType.UnitOfLength.parse(y),
                TType.UnitOfLength.parse(z),
            ),
            orient_type=orient_type,
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type="GLOBAL",
            constraint_axis=(False, False, False),
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff="SMOOTH",
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            release_confirm=True,
        ):
            raise Global.OperationCancelled(
                f"Cancelled operation MoveBy for xyz: {x, y, z}"
            )
        return self

    def RotateBy(
        self,
        x: TType.Angle = 0,
        y: TType.Angle = 0,
        z: TType.Angle = 0,
        orient_type: str = "GLOBAL",
        center_override=(0.0, 0.0, 0.0),
        **kwargs,
    ) -> Edit:
        """Apply rotation transform to objects mesh.
        If center_override is None it wont be contained in end
        rotation so center wont be overriden.

        Args:
            x (TType.Angle, optional): angle as float in radians or as str parsable by TType.Angle.parse
            y (TType.Angle, optional): angle as float in radians or as str parsable by TType.Angle.parse
            z (TType.Angle, optional): angle as float in radians or as str parsable by TType.Angle.parse
            orient_axis (str, optional): . Defaults to "X".
            orient_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
            orient_matrix_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"] Defaults to "GLOBAL".
        """
        if center_override is not None:
            kwargs["center_override"] = center_override
        x = TType.Angle.parse(x)
        y = TType.Angle.parse(y)
        z = TType.Angle.parse(z)
        if x:
            if "CANCELLED" in bpy.ops.transform.rotate(
                value=x,
                orient_axis="X",
                orient_type=orient_type,
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type="GLOBAL",
                constraint_axis=(False, False, False),
                mirror=True,
                use_proportional_edit=False,
                proportional_edit_falloff="SMOOTH",
                proportional_size=1,
                use_proportional_connected=False,
                use_proportional_projected=False,
                release_confirm=True,
                **kwargs,
            ):
                raise Global.OperationCancelled(
                    f"Cancelled operation RotateBy for X axis: {x}"
                )
        if y:
            if "CANCELLED" in bpy.ops.transform.rotate(
                value=y,
                orient_axis="Y",
                orient_type=orient_type,
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type="GLOBAL",
                constraint_axis=(False, False, False),
                mirror=True,
                use_proportional_edit=False,
                proportional_edit_falloff="SMOOTH",
                proportional_size=1,
                use_proportional_connected=False,
                use_proportional_projected=False,
                release_confirm=True,
                **kwargs,
            ):
                raise Global.OperationCancelled(
                    f"Cancelled operation RotateBy for Y axis: {y}"
                )
        if z:
            if "CANCELLED" in bpy.ops.transform.rotate(
                value=z,
                orient_axis="Z",
                orient_type=orient_type,
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type="GLOBAL",
                constraint_axis=(False, False, False),
                mirror=True,
                use_proportional_edit=False,
                proportional_edit_falloff="SMOOTH",
                proportional_size=1,
                use_proportional_connected=False,
                use_proportional_projected=False,
                release_confirm=True,
                **kwargs,
            ):
                raise Global.OperationCancelled(
                    f"Cancelled operation RotateBy for Z axis: {z}"
                )
        return self

    def ScaleBy(
        self,
        x: float = 1,
        y: float = 1,
        z: float = 1,
        orient_type: str = "GLOBAL",
        **kwargs,
    ) -> Edit:
        """Scale mesh.

        Args:
            x (float, optional) scale in x axis
            y (float, optional) scale in y axis
            z (float, optional) scale in z axis
            orient_type (str, optional): ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"]. Defaults to "GLOBAL".
            orient_matrix (tuple, optional): . Defaults to ((1, 0, 0), (0, 1, 0), (0, 0, 1)).
        """
        if "CANCELLED" in bpy.ops.transform.resize(
            value=(x, y, z),
            orient_type=orient_type,
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type="GLOBAL",
            constraint_axis=(False, False, False),
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff="SMOOTH",
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False,
            release_confirm=True,
            **kwargs,
        ):
            raise Global.OperationCancelled(f"Operation ScaleBy with xyz: {x, y, z}")
        return self


# $ <>=======================================================<>
# $              Object and global ops handlers
# $ <>=======================================================<>


class Object(Namespace):
    def MoveTo(bpy_obj, x: float = 0, y: float = 0, z: float = 0) -> BpyObject:
        """Move object to x, y, z by overwriting current transform.

        Args:
            x (float, optional): x axis trasform, as value accepted by TType.UnitsOfLength.parse(x). Defaults to 0.
            y (float, optional): y axis trasform, as value accepted by TType.UnitsOfLength.parse(y). Defaults to 0.
            z (float, optional): z axis trasform, as value accepted by TType.UnitsOfLength.parse(z). Defaults to 0.

        Returns:
            Object: self
        """
        bpy_obj.location.x = TType.UnitOfLength.parse(x)
        bpy_obj.location.y = TType.UnitOfLength.parse(y)
        bpy_obj.location.z = TType.UnitOfLength.parse(z)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        return bpy_obj

    def MoveBy(bpy_obj, x: float = 0, y: float = 0, z: float = 0) -> BpyObject:
        """Move object by x, y, z by adding to current transform.

        Args:
            x (float, optional): x axis trasform, as value accepted by TType.UnitsOfLength.parse(x). Defaults to 0.
            y (float, optional): y axis trasform, as value accepted by TType.UnitsOfLength.parse(y). Defaults to 0.
            z (float, optional): z axis trasform, as value accepted by TType.UnitsOfLength.parse(z). Defaults to 0.

        Returns:
            Object: self
        """
        bpy_obj.location.x += TType.UnitOfLength.parse(x)
        bpy_obj.location.y += TType.UnitOfLength.parse(y)
        bpy_obj.location.z += TType.UnitOfLength.parse(z)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        return bpy_obj

    def RotateTo(bpy_obj, x: float = 0, y: float = 0, z: float = 0) -> BpyObject:
        """Rotate by given angle (overwrite current rotation angle).

        Args:
            x (float, optional): x axis rotation as value accepted by TType.Angle.parse(x) . Defaults to 0.
            y (float, optional): y axis rotation as value accepted by TType.Angle.parse(y). Defaults to 0.
            z (float, optional): z axis rotation as value accepted by TType.Angle.parse(z). Defaults to 0.

        Returns:
            Object: self
        """
        bpy_obj.rotation_euler.x = TType.Angle.parse(x)
        bpy_obj.rotation_euler.y = TType.Angle.parse(y)
        bpy_obj.rotation_euler.z = TType.Angle.parse(z)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return bpy_obj

    def RotateBy(bpy_obj, x: float = 0, y: float = 0, z: float = 0) -> BpyObject:
        """Rotate by given angle (add value to current rotation angle).

        Args:
            x (float, optional): x axis rotation as value accepted by TType.Angle.parse(x) . Defaults to 0.
            y (float, optional): y axis rotation as value accepted by TType.Angle.parse(y). Defaults to 0.
            z (float, optional): z axis rotation as value accepted by TType.Angle.parse(z). Defaults to 0.

        Returns:
            Object: self
        """
        bpy_obj.rotation_euler.x += TType.Angle.parse(x)
        bpy_obj.rotation_euler.y += TType.Angle.parse(y)
        bpy_obj.rotation_euler.z += TType.Angle.parse(z)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return bpy_obj

    def ScaleTo(bpy_obj, x: float = 1, y: float = 1, z: float = 1) -> BpyObject:
        """Scale object to value. (overwrite current scale)

        Args:
            x (float, optional): x scale. Defaults to 1.
            y (float, optional): y scale. Defaults to 1.
            z (float, optional): z scale. Defaults to 1.

        Returns:
            Object: self
        """
        bpy_obj.scale.x = x
        bpy_obj.scale.y = y
        bpy_obj.scale.z = z
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return bpy_obj

    def ScaleBy(bpy_obj, x: float = 1, y: float = 1, z: float = 1) -> BpyObject:
        """Scale object by value. (multiply current scale)

        Args:
            x (float, optional): x scale. Defaults to 1.
            y (float, optional): y scale. Defaults to 1.
            z (float, optional): z scale. Defaults to 1.

        Returns:
            Object: self
        """
        bpy_obj.scale.x *= x
        bpy_obj.scale.y *= y
        bpy_obj.scale.z *= z
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return bpy_obj

    @staticmethod
    def TransformTo(
        bpy_obj: Object,
        location: tuple = None,
        rotation: tuple = None,
        scale: tuple = None,
    ):
        if location is not None:
            Object.MoveTo(
                bpy_obj,
                TType.UnitOfLength.parse(location[0]),
                TType.UnitOfLength.parse(location[1]),
                TType.UnitOfLength.parse(location[2]),
            )
        if rotation is not None:
            Object.RotateTo(
                bpy_obj,
                TType.Angle.parse(rotation[0]),
                TType.Angle.parse(rotation[1]),
                TType.Angle.parse(rotation[2]),
            )
        if scale is not None:
            Object.ScaleTo(bpy_obj, *scale)

    def duplicate(
        bpy_obj,
        x: TType.UnitOfLength = 0,
        y: TType.UnitOfLength = 0,
        z: TType.UnitOfLength = 0,
        linked: bool = False,
        orient_type: str = "GLOBAL",
    ) -> object:
        """Duplicates and translates object in object mode. Newly created object is both
        active and selected and no other object is.

        Args:
            xyz (tuple, optional): translation of object. Defaults to (0, 0, 0).
            linked (bool, optional): linkage presence. Defaults to True.
            orient_type (str, optional): one of ["GLOBAL", "LOCAL", "NORMAL", "GIMBAL", "VIEW", "CURSOR"]. Defaults to "GLOBAL".
        Returns:
            bpy_object: duplicate
        """
        x = TType.UnitOfLength.parse(x)
        y = TType.UnitOfLength.parse(y)
        z = TType.UnitOfLength.parse(z)
        Global.setActive(bpy_obj)
        Global.selectOnly(bpy_obj)
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={"linked": linked, "mode": "TRANSLATION"},
            TRANSFORM_OT_translate={
                "value": (x, y, z),
                "orient_type": orient_type,
                "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                "orient_matrix_type": "GLOBAL",
                "constraint_axis": (False, False, False),
                "mirror": True,
                "use_proportional_edit": False,
                "proportional_edit_falloff": "SMOOTH",
                "proportional_size": 1,
                "use_proportional_connected": False,
                "use_proportional_projected": False,
                "snap": False,
                "snap_target": "CLOSEST",
                "snap_point": (0, 0, 0),
                "snap_align": False,
                "snap_normal": (0, 0, 0),
                "gpencil_strokes": False,
                "cursor_transform": False,
                "texture_space": False,
                "remove_on_cancel": False,
                "release_confirm": False,
                "use_accurate": False,
                "use_automerge_and_split": False,
            },
        )
        return Global._Bpy_getActive()

    def bboxCenter(bpy_obj: Object) -> Vector:
        o = bpy_obj
        local_bbox_center = 0.125 * sum((Vector(b) for b in o.bound_box), Vector())
        global_bbox_center = o.matrix_world @ local_bbox_center
        return global_bbox_center

    def bboxMaxDist(bpy_obj: Object) -> float:
        o = bpy_obj
        bbox = [o.matrix_world @ Vector(b) for b in o.bound_box]
        max_dist = 0
        for vec in bbox:
            for val in vec:
                if abs(val) > max_dist:
                    max_dist = abs(val)
        return max_dist

    def bbox(bpy_obj: Object) -> float:
        o = bpy_obj
        return [o.matrix_world @ Vector(b) for b in o.bound_box]

    def convert(bpy_obj, target: str = "MESH") -> BpyObject:
        """Convert object from one type to another.

        Args:
            target (str, optional): target object type. Defaults to "MESH".
        """
        Global.setActive(bpy_obj)
        Global.selectOnly(bpy_obj)
        bpy.ops.object.convert(target=target)
        return bpy_obj

    def join(bpy_obj, *args: Object) -> BpyObject:
        """Joins all passed object into one at first object

        Returns:
            Object: joined object
        """
        Global.deselectAll()
        for o in args:
            if o != bpy_obj:
                Global.select(o)
        Global.setActive(bpy_obj)
        Global.select(bpy_obj)
        bpy.ops.object.join()
        return bpy_obj


class Camera:
    def __init__(
        self,
        location: tuple = (0, 0, 1),
        rotation: tuple = (0, 0, 0),
        scale: tuple = (1, 1, 1),
    ) -> None:
        """Object representing Camera with most significant camera properties available

        Args:
            location (tuple, optional): 3-tuple, values parsable by TType.UnitOfLength.parse(). Defaults to (0, 0, 1).
            rotation (tuple, optional): 3-tuple, values parsable by TType.Angle.parse(). Defaults to (0, 0, 0).
            scale (tuple, optional): 3-tuple of floats. Defaults to (1, 1, 1).
        """
        location = (
            TType.UnitOfLength.parse(location[0]),
            TType.UnitOfLength.parse(location[1]),
            TType.UnitOfLength.parse(location[2]),
        )
        rotation = (
            TType.Angle.parse(rotation[0]),
            TType.Angle.parse(rotation[1]),
            TType.Angle.parse(rotation[2]),
        )
        bpy.ops.object.camera_add(
            enter_editmode=False,
            align="VIEW",
            location=location,
            rotation=rotation,
            scale=scale,
        )
        self.camera = Global.getActive()

    def setMain(self):
        bpy.context.scene.camera = self.camera

    @property
    def type(self) -> str:
        return self.camera.data.type

    @type.setter
    def type(self, value: str) -> None:
        """Camera type

        Args:
            value (str): ["ORTHO", "PANO", "PERSP"]
        """
        self.camera.data.type = value

    @property
    def angle(self) -> float:
        return self.camera.data.angle

    @angle.setter
    def angle(self, value: float) -> None:
        self.camera.data.angle = value

    @property
    def ortho_scale(self) -> float:
        return self.camera.data.ortho_scale

    @ortho_scale.setter
    def ortho_scale(self, value: float) -> None:
        self.camera.data.ortho_scale = value

    @property
    def lens(self) -> float:
        return self.camera.data.lens

    @lens.setter
    def lens(self, value: float) -> None:
        self.camera.data.lens = value

    @property
    def clip_start(self) -> float:
        return self.camera.data.clip_start

    @clip_start.setter
    def clip_start(self, value: float) -> None:
        self.camera.data.clip_start = value

    @property
    def clip_end(self) -> float:
        return self.camera.data.clip_end

    @clip_end.setter
    def clip_end(self, value: float) -> None:
        self.camera.data.clip_end = value


# $ <>=======================================================<>
# $                    Modifiers handlers
# $ <>=======================================================<>
class Modifier:
    def Boolean(
        bpy_obj: Object,
        other: Object,
        operation: str = "DIFFERENCE",
        solver: str = "EXACT",
        use_self: bool = False,
    ) -> BpyObject:
        """
        Create instance of Boolean Blender modifier.

        Args:
            other (object): blender object to be used as modifier object.
            operation (str, optional): ["DIFFERENCE", "INTERSECT", "UNION"]. Defaults to "DIFFERENCE".
            solver (str, optional): ["FAST", "EXACT]. Defaults to "EXACT".
            use_self (bool, optional): [description]. Defaults to False.

        Returns:
            BlenderModifier: self
        """
        if Edit.isEditMode():
            raise RuntimeError("You cannot add modifiers in edit mode.")
        MODIFIER = bpy_obj.modifiers.new(f"__BOOL_MOD_{Global.Unique()}__", "BOOLEAN")
        MODIFIER.object = other
        MODIFIER.operation = operation
        MODIFIER.solver = solver
        MODIFIER.use_self = use_self
        Global.selectOnly(bpy_obj)
        Global.setActive(bpy_obj)
        bpy.ops.object.modifier_apply(modifier=MODIFIER.name)
        return bpy_obj

    def Array(
        bpy_obj: Object,
        offset_x: float = 0,
        offset_y: float = 0,
        offset_z: float = 0,
        count: int = 1,
        use_relative_offset: bool = False,
        use_constant_offset: bool = True,
    ) -> BpyObject:
        """
        Create instance of Array Blender modifier.

        Args:
            offset_x (float, optional): . 0.
            offset_y (float, optional): . 0.
            offset_z (float, optional): . 0.
            count (int, optional): . Defaults to 1.
            use_relative_offset (bool, optional): . Defaults to False.
            use_constant_offset (bool, optional): . Defaults to True.

        Returns:
            BlenderModifier: self
        """
        if Edit.isEditMode():
            raise RuntimeError("You cannot add modifiers in edit mode.")
        MODIFIER = bpy_obj.modifiers.new(f"__ARRAY_MOD_{Global.Unique()}__", "ARRAY")
        MODIFIER.use_relative_offset = use_relative_offset
        MODIFIER.use_constant_offset = use_constant_offset
        MODIFIER.constant_offset_displace[0] = offset_x
        MODIFIER.constant_offset_displace[1] = offset_y
        MODIFIER.constant_offset_displace[2] = offset_z
        MODIFIER.count = count
        Global.selectOnly(bpy_obj)
        Global.setActive(bpy_obj)
        bpy.ops.object.modifier_apply(modifier=MODIFIER.name)
        return bpy_obj

    def SimpleDeform(
        bpy_obj: Object,
        deform_method: str = "BEND",
        deform_axis: str = "X",
        angle: float = math.pi / 4,
        limits: tuple = (0.0, 1.0),
    ) -> BpyObject:
        """
        Create instance of Simple Deform Blender modifier.

        Args:
            deform_method (str, optional): ["TWIST", "BEND", "TAPER", "STRETCH"]. Defaults to "BEND".
            deform_axis (str, optional): "X", "Y", "Z". Defaults to "X".
            angle (float, optional): Angle in radians. Defaults to pi/4.
            limits (Tuple[float, float], optional): Defaults to (0.0, 1.0).
        Returns:
            BlenderModifier: self
        """
        if Edit.isEditMode():
            raise RuntimeError("You cannot add modifiers in edit mode.")
        MODIFIER = bpy_obj.modifiers.new(
            f"__SD_MOD_{Global.Unique()}__", "SIMPLE_DEFORM"
        )
        MODIFIER.deform_method = deform_method
        MODIFIER.deform_axis = deform_axis
        MODIFIER.angle = angle
        MODIFIER.limits = limits
        Global.selectOnly(bpy_obj)
        Global.setActive(bpy_obj)
        bpy.ops.object.modifier_apply(modifier=MODIFIER.name)
        return bpy_obj

    def Solidify(
        bpy_obj: Object,
        thickness: float = 0.01,
        offset: float = -1,
        use_even_offset: bool = False,
        use_quality_normals: bool = True,
    ) -> BpyObject:
        """
        Create instance of Solidify Blender modifier.

        Args:
            this (object): blender object to create modifier for.
            thickness (float, optional): tickness of solidification. Defaults to 0.01.
            offset (float, optional): offset from center of plane. Defaults to -1.
            use_even_offset (bool, optional): . Defaults to False.

        Returns:
            BlenderModifier: self
        """
        if Edit.isEditMode():
            raise RuntimeError("You cannot add modifiers in edit mode.")
        MODIFIER = bpy_obj.modifiers.new(
            f"__SOLIDIFY_MOD_{Global.Unique()}__", "SOLIDIFY"
        )
        MODIFIER.thickness = thickness
        MODIFIER.offset = offset
        MODIFIER.use_even_offset = use_even_offset
        MODIFIER.use_quality_normals = use_quality_normals

        Global.selectOnly(bpy_obj)
        Global.setActive(bpy_obj)
        bpy.ops.object.modifier_apply(modifier=MODIFIER.name)
        return bpy_obj

    def Bevel(
        bpy_obj: Object,
        affect: str = "EDGES",
        offset_type: str = "OFFSET",
        width: TType.UnitOfLength = 0.1,
        segments: int = 1,
        limit_method: str = "NONE",
        angle_limit: str = "30deg",
        use_clamp_overlap: bool = True,
    ) -> BpyObject:
        """Applies blender Bevel modifier on to object represented by this.

        Args:
            affect (str, optional): ["VERTICES", "EDGES"]. Defaults to "EDGES".
            offset_type (str, optional):  Defaults to "OFFSET".
            width (float, optional): . Defaults to 0.1.
            segments (int, optional): . Defaults to 1.
            limit_method (str, optional): ['NONE', 'ANGLE', 'WEIGHT', 'VGROUP'] Defaults to "NONE".
            angle_limit (str, optional): . Defaults to "30deg".

        Returns:
            BlenderModifier: self
        """
        if Edit.isEditMode():
            raise RuntimeError("You cannot add modifiers in edit mode.")
        MODIFIER = bpy_obj.modifiers.new(f"__BEVEL_MOD_{Global.Unique()}__", "BEVEL")
        MODIFIER.affect = affect
        MODIFIER.offset_type = offset_type
        MODIFIER.width = TType.UnitOfLength.parse(width)
        MODIFIER.segments = segments
        MODIFIER.limit_method = limit_method
        MODIFIER.angle_limit = TType.Angle.parse(angle_limit)
        MODIFIER.use_clamp_overlap = use_clamp_overlap

        Global.selectOnly(bpy_obj)
        Global.setActive(bpy_obj)
        bpy.ops.object.modifier_apply(modifier=MODIFIER.name)
        return bpy_obj


# $ <>=======================================================<>
# $                     Materials handlers
# $ <>=======================================================<>


class MaterialNodes(Namespace):
    class NodeIO:
        def __init__(self, material) -> None:
            self.material = material.bpy_material
            self.node = material.node

        @property
        def inputs(self) -> list:
            return self.node.inputs

        @property
        def outputs(self) -> list:
            return self.node.outputs

    class Node(ABC):
        NODE_CLASS: str = None
        EXISTING_NAME: str = None
        input: MaterialNodes.NodeIO
        output: MaterialNodes.NodeIO

        def __init__(self, material: Material, **kwargs) -> None:
            self.material = material
            if self.EXISTING_NAME is not None:
                self.node = self.bpy_material.node_tree.nodes[self.EXISTING_NAME]
            else:
                self.node = self.bpy_material.node_tree.nodes.new(type=self.NODE_CLASS)
            self.update(**kwargs)

        @abstractmethod
        def update(self, *args, **kwargs) -> Material:
            return self.material

        @property
        def bpy_material(self):
            return self.material.bpy_material

        @property
        def name(self) -> str:
            return self.node.name

        @name.setter
        def name(self, value: str) -> None:
            self.node.name = value

        @property
        def inputs(self) -> list:
            return self.node.inputs

        @property
        def outputs(self) -> list:
            return self.node.outputs

    class BSDF_node(Node):
        EXISTING_NAME: str = "Principled BSDF"

        def __init__(self, material: Material, **kwargs) -> None:
            super().__init__(material, **kwargs)

            class BSDF_node_input(MaterialNodes.NodeIO):
                @property
                def color(self) -> MaterialNodes.Node.input:
                    return self.inputs[0]

                @color.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[0], node_output)

                @property
                def subsurface(self) -> MaterialNodes.Node.input:
                    return self.inputs[1]

                @subsurface.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[1], node_output)

                @property
                def subsurfaceRadius(self) -> MaterialNodes.Node.input:
                    return self.inputs[2]

                @subsurfaceRadius.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[2], node_output)

                @property
                def subsurfaceColor(self) -> MaterialNodes.Node.input:
                    return self.inputs[3]

                @subsurfaceColor.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[3], node_output)

                @property
                def metallic(self) -> MaterialNodes.Node.input:
                    return self.inputs[4]

                @metallic.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[4], node_output)

                @property
                def specular(self) -> MaterialNodes.Node.input:
                    return self.inputs[5]

                @specular.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[5], node_output)

                @property
                def specularTint(self) -> MaterialNodes.Node.input:
                    return self.inputs[6]

                @specularTint.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[6], node_output)

                @property
                def roughness(self) -> MaterialNodes.Node.input:
                    return self.inputs[7]

                @roughness.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[7], node_output)

                @property
                def anisotropic(self) -> MaterialNodes.Node.input:
                    return self.inputs[8]

                @anisotropic.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[8], node_output)

                @property
                def anisotropicRotation(self) -> MaterialNodes.Node.input:
                    return self.inputs[9]

                @anisotropicRotation.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[9], node_output)

                @property
                def sheen(self) -> MaterialNodes.Node.input:
                    return self.inputs[10]

                @sheen.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[10], node_output)

                @property
                def sheenTint(self) -> MaterialNodes.Node.input:
                    return self.inputs[11]

                @sheenTint.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[11], node_output)

                @property
                def clearcoat(self) -> MaterialNodes.Node.input:
                    return self.inputs[12]

                @clearcoat.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[12], node_output)

                @property
                def clearcoatRoughness(self) -> MaterialNodes.Node.input:
                    return self.inputs[13]

                @clearcoatRoughness.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[13], node_output)

                @property
                def IOR(self) -> MaterialNodes.Node.input:
                    return self.inputs[14]

                @IOR.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[14], node_output)

                @property
                def transmission(self) -> MaterialNodes.Node.input:
                    return self.inputs[15]

                @transmission.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[15], node_output)

                @property
                def transmissionRoughness(self) -> MaterialNodes.Node.input:
                    return self.inputs[16]

                @transmissionRoughness.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[16], node_output)

                @property
                def emission(self) -> MaterialNodes.Node.input:
                    return self.inputs[17]

                @emission.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[17], node_output)

                @property
                def emissionStrength(self) -> MaterialNodes.Node.input:
                    return self.inputs[18]

                @emissionStrength.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[18], node_output)

                @property
                def alpha(self) -> MaterialNodes.Node.input:
                    return self.inputs[19]

                @alpha.setter
                def f(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[19], node_output)

            self.input: BSDF_node_input = BSDF_node_input(self)

            class BSDF_node_output(MaterialNodes.NodeIO):
                @property
                def BSDF(self) -> MaterialNodes.Node.output:
                    return self.outputs[0]

                @BSDF.setter
                def f(self, node_input: MaterialNodes.Node.input) -> None:
                    self.material.node_tree.links.new(self.outputs[0], node_input)

            self.output: BSDF_node_output = BSDF_node_output(self)

        def update(
            self,
            color: TType.Color = None,
            subsurface: float = None,
            subsurfaceRadius: tuple = None,
            subsurfaceColor: TType.Color = None,
            metallic: float = None,
            specular: float = None,
            specularTint: float = None,
            roughness: float = None,
            anisotropic: float = None,
            anisotropicRotation: float = None,
            sheen: float = None,
            sheenTint: float = None,
            clearcoat: float = None,
            clearcoatRoughness: float = None,
            IOR: float = None,
            transmission: float = None,
            transmissionRoughness: float = None,
            emission: TType.Color = None,
            emissionStrength: float = None,
            alpha: float = None,
        ) -> Material:
            """[summary]

            Args:
                color (tuple, optional): Surface color TType.Color.parse(color). Defaults to (0.0, 0.0, 0.0, 1.0).
                subsurface (float, optional): . Defaults to 0.0.
                subsurfaceRadius (tuple, optional): . Defaults to (0.0, 0.0, 0.0, 1.0).
                subsurfaceColor (TType.Color, optional): TType.Color.parse(color). Defaults to (0.0, 0.0, 0.0, 1.0).
                metallic (float, optional): Metallicness of surface. Defaults to 0.0.
                specular (float, optional): . Defaults to 0.5.
                specularTint (float, optional): . Defaults to 0.0.
                roughness (float, optional): Roughness of surface. Defaults to 1.0.
                anisotropic (float, optional): . Defaults to 0.0.
                anisotropicRotation (float, optional): . Defaults to 0.0.
                sheen (float, optional): . Defaults to 0.0.
                sheenTint (float, optional): . Defaults to 0.5.
                clearcoat (float, optional): . Defaults to 0.0.
                clearcoatRoughness (float, optional): . Defaults to 0.030.
                IOR (float, optional): . Defaults to 1.450.
                transmission (float, optional): . Defaults to 0.0.
                transmissionRoughness (float, optional): . Defaults to 0.0.
                emission (tuple, optional): TType.Color.parse(color). Defaults to (0.0, 0.0, 0.0, 1.0).
                emissionStrength (float, optional): . Defaults to 1.0.
                alpha (float, optional): . Defaults to 1.0.
            """
            if color is not None:
                self.inputs[0].default_value = TType.Color.parse(color)
            if subsurface is not None:
                self.inputs[1].default_value = subsurface
            if subsurfaceRadius is not None:
                self.inputs[2].default_value[0] = subsurfaceRadius[0]
                self.inputs[2].default_value[1] = subsurfaceRadius[1]
                self.inputs[2].default_value[2] = subsurfaceRadius[2]
            if subsurfaceColor is not None:
                self.inputs[3].default_value = TType.Color.parse(subsurfaceColor)
            if metallic is not None:
                self.inputs[4].default_value = metallic
            if specular is not None:
                self.inputs[5].default_value = specular
            if specularTint is not None:
                self.inputs[6].default_value = specularTint
            if roughness is not None:
                self.inputs[7].default_value = roughness
            if anisotropic is not None:
                self.inputs[8].default_value = anisotropic
            if anisotropicRotation is not None:
                self.inputs[9].default_value = anisotropicRotation
            if sheen is not None:
                self.inputs[10].default_value = sheen
            if sheenTint is not None:
                self.inputs[11].default_value = sheenTint
            if clearcoat is not None:
                self.inputs[12].default_value = clearcoat
            if clearcoatRoughness is not None:
                self.inputs[13].default_value = clearcoatRoughness
            if IOR is not None:
                self.inputs[14].default_value = IOR
            if transmission is not None:
                self.inputs[15].default_value = transmission
            if transmissionRoughness is not None:
                self.inputs[16].default_value = transmissionRoughness
            if emission is not None:
                self.inputs[17].default_value = TType.Color.parse(emission)
            if emissionStrength is not None:
                self.inputs[18].default_value = emissionStrength
            if alpha is not None:
                self.inputs[19].default_value = alpha
            return self.material

    class INVERT_node(Node):
        NODE_CLASS: str = "ShaderNodeInvert"

        def __init__(self, material: Material, **kwargs) -> None:
            super().__init__(material, **kwargs)

            class INVERT_node_input(MaterialNodes.NodeIO):
                @property
                def factor(self) -> MaterialNodes.Node.input:
                    return self.inputs[0]

                @factor.setter
                def factor(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[0], node_output)

                @property
                def color(self) -> MaterialNodes.Node.input:
                    return self.inputs[1]

                @color.setter
                def color(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.inputs[1], node_output)

            self.input: INVERT_node_input = INVERT_node_input(self)

            class INVERT_node_output(MaterialNodes.NodeIO):
                @property
                def color(self) -> MaterialNodes.Node.output:
                    return self.outputs[0]

                @color.setter
                def color(self, node_input: MaterialNodes.Node.input) -> None:
                    self.material.node_tree.links.new(self.outputs[0], node_input)

            self.output: INVERT_node_output = INVERT_node_output(self)

        def update(
            self,
            factor: float = None,
            color: TType.Color = None,
        ) -> Material:
            """Update Invert node represented by this object.

            Args:
                factor (float, optional): scale factor. Defaults to 1.0.
                color (TType.Color.parse, optional): color to invert. Defaults to (0.0,0.0,0.0,1.0).
            """
            if factor is not None:
                self.inputs[0].default_value = factor
            if color is not None:
                self.inputs[1].default_value = TType.Color.parse(color)
            return self.material

    class MATERIAL_OUTPUT_node(Node):
        EXISTING_NAME: str = "Material Output"

        def __init__(self, material: Material, **kwargs) -> None:
            super().__init__(material, **kwargs)

            class OUTPUT_node_node_input(MaterialNodes.NodeIO):
                @property
                def surface(self) -> MaterialNodes.Node.input:
                    return self.node.inputs[0]

                @surface.setter
                def surface(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.node.inputs[0], node_output)

                @property
                def volume(self) -> MaterialNodes.Node.input:
                    return self.node.inputs[1]

                @volume.setter
                def volume(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.node.inputs[1], node_output)

                @property
                def displacement(self) -> MaterialNodes.Node.input:
                    return self.node.inputs[2]

                @displacement.setter
                def displacement(self, node_output: MaterialNodes.Node.output) -> None:
                    self.material.node_tree.links.new(self.node.inputs[2], node_output)

            self.input: OUTPUT_node_node_input = OUTPUT_node_node_input(self)

            class OUTPUT_node_node_output(MaterialNodes.NodeIO):
                pass

            self.output: OUTPUT_node_node_output = OUTPUT_node_node_output(self)

        def update(self, **kwargs) -> Material:
            """This node do not have any IO that can be updated."""
            if len(kwargs):
                raise RuntimeError(
                    "MATERIAL_OUTPUT_node do not have any IO that can be updated."
                )
            return self.material


class Material:
    bpy_material: object

    def __init__(self, bpy_obj: Object = None) -> None:
        if bpy_obj is None or len(bpy_obj.data.materials.keys()) == 0:
            self.bpy_material = bpy.data.materials.new(name=f"{Global.Unique()}")
            self.bpy_material.use_nodes = True
            if bpy_obj is not None:
                self.assign(bpy_obj)
        else:
            self.bpy_material = self.bpy_obj.data.materials[0]
            self.bpy_material.use_nodes = True
        self.BSDF_node = MaterialNodes.BSDF_node(self)
        self.update = self.BSDF_node.update
        self.OUTPUT_node = MaterialNodes.MATERIAL_OUTPUT_node(self)

    def assign(self, bpy_obj) -> Material:
        bpy_obj.data.materials.append(self.bpy_material)
        return self

    @property
    def node_tree(self) -> dict:
        return self.bpy_material.node_tree

    def new(self, node_type: MaterialNodes.Node):
        return node_type(self)

    @staticmethod
    def Smooth(bpy_obj):
        with Edit(bpy_obj) as edit:
            for face in edit.faces:
                face.smooth = True


'''
class Material(Namespace):
    @staticmethod
    def newMaterial():
        """Create new material instance with nodes turned on.

        Returns:
            object: Blender material object.
        """
        MATERIAL = bpy.data.materials.new(name=f"{Blender.getCode()}")
        MATERIAL.use_nodes = True
        return MATERIAL

    @staticmethod
    def newNode(material: object, type: str = "ShaderNodeTexImage", **kwargs):
        """Create new instance of node of given type for given material.

        Args:
            material (object): blender material object.
            type (str, optional): type of node. Defaults to "ShaderNodeTexImage".
        """
        node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        node.__dict__.update(kwargs)

    class TextureImage:
        def __init__(self, material: object, **kwargs):
            self._material = material
            self._node = self._material.node_tree.nodes.new(
                type="ShaderNodeTexImage"
            )
            self.update(**kwargs)

        @property
        def color(self):
            return self._node.outputs[0]

        @property
        def alpha(self):
            return self._node.outputs[1]

        @property
        def vector(self):
            return self._node.inputs[0]

        def update(
            self,
            image: object = None,
            interpolation: str = None,
            projection: str = None,
            projection_blend: float = None,
            extension: str = None,
        ):
            """Update node property, if passed value is None, value is not changed

            Args:
                image (object): Blender Image object.
                interpolation (str, optional): one of ["Linear", "Cubic", "Closest", "Smart"]. Defaults to "Cubic".
                projection (str, optional): one of ["FLAT", "BOX", "SPHERE", "TUBE"]. Defaults to "Cubic".
                extension (str, optional): one of ["REPEAT", "EXTEND", "CLIP"]. Defaults to "REPEAT".
            """
            if image is not None:
                self._node.image = image
            if interpolation is not None:
                self._node.interpolation = interpolation
            if projection is not None:
                self._node.projection = projection
            if projection_blend is not None:
                self._node.projection_blend = projection_blend
            if extension is not None:
                self._node.extension = extension

        def linkInput(self, vector: object = None):
            """Link coresponding input of TextureImage node to output of another node.

            Args:
                vector (object, optional): Other nodes output. Defaults to None.
            """
            if vector is not None:
                self._material.node_tree.links.new(self.vector, vector)

        def linkOutput(
            self,
            color: object = None,
            alpha: object = None,
        ):
            """Link coresponding output of TextureImage node to output of another node.

            Args:
                color (object, optional): Other nodes output. Defaults to None.
                alpha (object, optional): Other nodes output. Defaults to None.
            """
            if color is not None:
                self._material.node_tree.links.new(color, self.color)
            if alpha is not None:
                self._material.node_tree.links.new(alpha, self.alpha)

    class SeparateRGB:
        def __init__(self, material: object):
            self._material = material
            self._node = self._material.node_tree.nodes.new(
                type="ShaderNodeSeparateRGB"
            )

        @property
        def image(self):
            return self._node.inputs[0]

        @property
        def R(self):
            return self._node.outputs[0]

        @property
        def G(self):
            return self._node.outputs[1]

        @property
        def B(self):
            return self._node.outputs[2]

        def linkInput(self, image: object = None):
            if image is not None:
                self._material.node_tree.links.new(self.image, image)

        def linkOutput(
            self,
            R: object = None,
            G: object = None,
            B: object = None,
        ):
            if R is not None:
                self._material.node_tree.links.new(R, self.R)
            if G is not None:
                self._material.node_tree.links.new(G, self.G)
            if G is not None:
                self._material.node_tree.links.new(B, self.B)

'''

# $ <>=======================================================<>
# $              Mesh object creation handlers
# $ <>=======================================================<>


class LowLevel(Namespace):
    @staticmethod
    def fromPyData(
        vertexData: list = None, edgeData: list = None, faceData: list = None
    ) -> BpyObject:
        if vertexData is None:
            vertexData = []
        if edgeData is None:
            edgeData = []
        if faceData is None:
            faceData = []
        mesh = bpy.data.meshes.new(Global.Unique())
        mesh.from_pydata(vertexData, edgeData, faceData)
        mesh.update()
        obj = bpy.data.objects.new(Global.Unique(), mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj

    @staticmethod
    def makeArc(
        radius: TType.UnitOfLength,
        begin: TType.Angle,
        end: TType.Angle,
        vertices: int = 32,
        center_point: bool = False,
    ) -> BpyObject:
        radius = TType.UnitOfLength.parse(radius)
        begin = TType.Angle.parse(begin)
        end = TType.Angle.parse(end)

        vertices = int((abs(end - begin) / (2 * math.pi)) * vertices)

        fx = lambda alpha: radius * math.cos(alpha)
        fy = lambda alpha: radius * math.sin(alpha)
        vd = [
            (fx(alpha), fy(alpha), 0) for alpha in numpy.linspace(begin, end, vertices)
        ]
        if center_point:
            vd.append((0, 0, 0))
        return LowLevel.fromPyData(
            vd,
            [(index, index + 1) for index in range(vertices - 1)],
        )

    @staticmethod
    def LShape(
        x: float = 1.0,
        y: float = 0.2,
        z: float = 1.0,
        boostZ: float = 0.1,
        radius: float = 0.5,
        vertices: int = 16,
    ) -> BpyObject:
        begin = TType.Angle.parse("270deg")
        end = TType.Angle.parse("360deg")
        y /= 2
        fx = lambda alpha: radius * math.cos(alpha)
        fz = lambda alpha: radius * math.sin(alpha)

        if 0 < boostZ < (z - radius):
            vb_prefix = [(0, y, 0), (0, y, boostZ - z * 10e-4), (0, y, boostZ)]
        else:
            vb_prefix = [(0, y, 0)]

        vd = (
            vb_prefix
            + [
                (fz(alpha) + radius, y, fx(alpha) + z - radius)
                for alpha in numpy.linspace(begin, end, vertices)
            ]
            + [(x, y, z)]
        )
        return LowLevel.fromPyData(
            vd,
            [(index, index + 1) for index in range(len(vd) - 1)],
        )

    @staticmethod
    def SShape(
        x: float = 1.0,  # length
        y: float = 0.2,  # width
        z: float = 1.0,  # height
        th: float = 0.1,  # thickness
        vertices: int = 16,
    ) -> BpyObject:
        pi_half = math.pi / 2
        y_half = y / 2
        th_half = th / 2
        height = z - th_half
        sin_height = (z - th) / 2
        vd = (
            [(0, y_half, th_half)]
            + [
                (
                    x * 0.25 + x * val * 0.5,
                    y_half,
                    math.sin(val * math.pi - pi_half) * sin_height
                    + sin_height
                    + th_half,
                )
                for val in numpy.linspace(0, 1, vertices)
            ]
            + [(x, y_half, height)]
        )
        return LowLevel.fromPyData(
            vd,
            [(index, index + 1) for index in range(len(vd) - 1)],
        )


class Mesh(Namespace):
    def Rectangle(
        x_size: TType.UnitOfLength = 1.0,
        y_size: TType.UnitOfLength = 1.0,
        z_size: TType.UnitOfLength = 0.0,
        location: tuple = None,
        rotation: tuple = None,
        scale: tuple = None,
        *,
        material: dict = None,
    ) -> BpyObject:
        """This class is able to create both flat Rectangle (for z_size = 0)
        and cuboid (with any other value for z_size)

        Args:
            x_size (TType.UnitOfLength, optional): Value that can be parsed by TType.UnitsOfLength.parse(). Defaults to 1.
            y_size (TType.UnitOfLength, optional): Value that can be parsed by TType.UnitsOfLength.parse(). Defaults to 1.
            z_size (TType.UnitOfLength, optional): Value that can be parsed by TType.UnitsOfLength.parse(). Defaults to 1.
            location (tuple, 3xTType.UnitOfLength): initial location of object
            rotation (tuple, 3xTType.Angle): initial rotation of object
            scale (tuple, 3xfloat): initial scale of object
        """
        x_size = TType.UnitOfLength.parse(x_size)
        y_size = TType.UnitOfLength.parse(y_size)
        z_size = TType.UnitOfLength.parse(z_size)
        bpy.ops.mesh.primitive_plane_add(
            size=1,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
        )
        bpy_obj = Global._Bpy_getActive()
        if z_size:
            Edit(bpy_obj).enter().extrude(z=1).exit()
        Object.ScaleBy(bpy_obj, x_size, y_size, z_size)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def Circle(
        x_size: TType.UnitOfLength = 1.0,
        y_size: TType.UnitOfLength = 1.0,
        z_size: TType.UnitOfLength = 0.0,
        fill_type: str = "NGON",
        vertices: int = 24,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        """
        Args:
            x_size (TType.UnitOfLength.parse, optional): Value that can be parsed by TType.UnitsOfLength.parse(). Defaults to 1.
            y_size (TType.UnitOfLength.parse, optional): Value that can be parsed by TType.UnitsOfLength.parse(). Defaults to 1.
            z_size (TType.UnitOfLength.parse, optional): Value that can be parsed by TType.UnitsOfLength.parse(). Defaults to 1.
            vertices (int, optional): Defaults to 32.
            fill_type (str, optional): one of ["NGON", "TRIFAN", "NOTHING"] Defaults to "NOTHING".
        """
        x_size = TType.UnitOfLength.parse(x_size)
        y_size = TType.UnitOfLength.parse(y_size)
        z_size = TType.UnitOfLength.parse(z_size)
        bpy.ops.mesh.primitive_circle_add(
            vertices=vertices,
            radius=0.5,
            fill_type=fill_type,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
        )
        bpy_obj = Global._Bpy_getActive()
        if z_size:
            Edit(bpy_obj).enter().extrude(z=1).exit()
        Object.ScaleBy(bpy_obj, x_size, y_size, z_size)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def Obround(
        radius: TType.UnitOfLength = 0.5,
        x_size: TType.UnitOfLength = 2.0,
        z_size: TType.UnitOfLength = 0,
        vertices: int = 32,
        center_point: bool = False,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        radius = TType.UnitOfLength.parse(radius)
        x_size = TType.UnitOfLength.parse(x_size)
        z_size = TType.UnitOfLength.parse(z_size)
        # left arc of obround
        left_arc = LowLevel.makeArc(radius, "90deg", "-90deg", vertices, center_point)
        # right arc of obround
        right_arc = LowLevel.makeArc(radius, "90deg", "270deg", vertices, center_point)
        right_arc.location = (-x_size, 0, 0)
        # select both and join them
        Global._Bpy_deselectAll()
        Global._Bpy_setActive(left_arc)
        left_arc.select_set(True)
        right_arc.select_set(True)
        bpy.ops.object.join()
        bpy_obj = left_arc
        with Edit(bpy_obj) as edit:
            edit.selectAll()
            edit.makeEdgeFace()
            edit.MoveBy(x_size / 2)
            if z_size:
                edit.extrude(z=z_size)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def Arc(
        radius: TType.UnitOfLength = 0.5,
        begin_angle: TType.Angle = "0deg",
        end_angle: TType.Angle = "360deg",
        z_size: TType.UnitOfLength = 0,
        vertices: int = 32,
        center_point: bool = False,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        bpy_obj = LowLevel.makeArc(
            radius, begin_angle, end_angle, vertices, center_point
        )
        with Edit(bpy_obj) as edit:
            edit.selectAll()
            edit.makeEdgeFace()
            if z_size:
                edit.extrude(z=z_size)
        bpy_obj = Global._Bpy_getActive()
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def Text(
        text: str = "Text",
        font: str = "",
        size: float = 1.0,
        depth: float = 0.0,
        align_x: str = "CENTER",
        align_y: str = "CENTER",
        resolution: int = 10,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        bpy.ops.object.text_add(
            radius=1.0,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
        )
        bpy_obj = Global._Bpy_getActive()
        bpy_obj.data.body = text
        bpy_obj.data.resolution_u = resolution
        bpy_obj.data.align_x = align_x
        bpy_obj.data.align_y = align_y
        bpy_obj.data.extrude = depth
        bpy_obj.data.size = size
        if font:
            bpy_obj.data.font = bpy.data.fonts.load(font)
        Object.convert(bpy_obj, "MESH")
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def UVSphere(
        segments: int = 32,
        ring_count: int = 16,
        radius: TType.UnitOfLength = 1.0,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        """
        Args:
            segments (int, optional): horizontal segments. Defaults to 32.
            ring_count (int, optional): vertical rings count. Defaults to 16.
            radius (TType.UnitOfLength, optional): sphere radius. Defaults to 1.0.
            material (dict, optional): BSDF node params as dict. Defaults to None.
        """
        radius = TType.UnitOfLength.parse(radius)
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments,
            ring_count=ring_count,
            radius=radius,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
        )
        bpy_obj = Global._Bpy_getActive()
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def LShape(
        height: TType.UnitOfLength = 1.0,
        length: TType.UnitOfLength = 1.0,
        thickness: TType.UnitOfLength = 0.05,
        width: TType.UnitOfLength = 0.1,
        boostHeight: TType.UnitOfLength = 0,
        boostWidth: TType.UnitOfLength = 0,
        radius: TType.UnitOfLength = 0.1,
        vertices: float = 16,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        height = TType.UnitOfLength.parse(height)
        length = TType.UnitOfLength.parse(length)
        thickness = TType.UnitOfLength.parse(thickness)
        width = TType.UnitOfLength.parse(width)
        boostHeight = TType.UnitOfLength.parse(boostHeight)
        boostWidth = TType.UnitOfLength.parse(boostWidth)
        radius = TType.UnitOfLength.parse(radius)
        bpy_obj = LowLevel.LShape(
            length,
            width,
            height,
            boostHeight,
            radius,
            vertices,
        )
        with Edit(bpy_obj) as edit:
            edit.selectAll()
            edit.extrude(y=-width)
            if boostWidth or boostHeight:
                for edge in edit.edges:
                    edge.select = (
                        edge.calc_length() > 0
                        and edge.verts[0].co.z >= boostHeight - height * 0.5 * 10e-4
                        and edge.verts[1].co.z >= boostHeight - height * 0.5 * 10e-4
                    )
                edit.ScaleBy(y=boostWidth / width)
            edit.selectAll()
            edit.MoveBy(x=-length / 2)
        Modifier.Solidify(bpy_obj, thickness, 1, True)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    def SShape(
        height: TType.UnitOfLength = 1.0,
        length: TType.UnitOfLength = 1.0,
        thickness: TType.UnitOfLength = 0.1,
        width: TType.UnitOfLength = 0.2,
        vertices: float = 16,
        *,
        material: dict = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        height = TType.UnitOfLength.parse(height)
        length = TType.UnitOfLength.parse(length)
        thickness = TType.UnitOfLength.parse(thickness)
        width = TType.UnitOfLength.parse(width)
        bpy_obj = LowLevel.SShape(
            length,
            width,
            height,
            thickness,
            vertices,
        )
        with Edit(bpy_obj) as edit:
            edit.selectAll()
            edit.extrude(y=-width)
            edit.selectAll()
            edit.MoveBy(x=-length / 2)
        Modifier.Solidify(bpy_obj, thickness, 0, True)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return Global._Bpy_getActive()

    @staticmethod
    def IndentedCylinder(
        height: TType.UnitOfLength = 1.0,
        radius: TType.UnitOfLength = 0.5,
        vertices: int = 32,
        indents: List[
            Tuple[float, float, float]
        ] = None,  # [(ring_center_offset, ring_height, depth), ...]
        material: TType.MaterialParams = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        height = TType.UnitOfLength.parse(height)
        radius = TType.UnitOfLength.parse(radius)
        bpy_obj = Mesh.Circle(radius * 2, radius * 2, vertices=vertices)
        with Edit(bpy_obj) as edit:
            elevation = 0
            if indents is not None:
                for ring_center_offset, ring_height, depth in sorted(
                    indents, key=lambda item: item[0]
                ):
                    ring_center_offset = (ring_center_offset - ring_height / 2) * height
                    if elevation > ring_center_offset:
                        break
                    elif elevation < ring_center_offset:
                        edit.extrude(0, 0, ring_center_offset - elevation)
                        elevation += ring_center_offset - elevation
                    ring_height *= height
                    edit.extrude(0, 0, ring_height / 2)
                    scl = (radius - depth) / radius
                    edit.ScaleBy(scl, scl, 1)
                    edit.extrude(0, 0, ring_height / 2)
                    edit.ScaleBy(1 / scl, 1 / scl, 1)
                    elevation += ring_height
            if elevation < height:
                edit.extrude(0, 0, height - elevation)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    @staticmethod
    def BeveledCube(
        sizeX: TType.UnitOfLength = 1.0,
        sizeY: TType.UnitOfLength = 1.0,
        sizeZ: TType.UnitOfLength = 1.0,
        topEdgeRing: Tuple[int, float] = None,
        sideEdges: Tuple[int, float] = None,
        botEdgeRing: Tuple[int, float] = None,
        material: TType.MaterialParams = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ) -> BpyObject:
        sizeX = TType.UnitOfLength.parse(sizeX)
        sizeY = TType.UnitOfLength.parse(sizeY)
        sizeZ = TType.UnitOfLength.parse(sizeZ)
        bpy_obj = Mesh.Rectangle(sizeX, sizeY, sizeZ)
        Object.MoveBy(bpy_obj, z=-0.5)
        tz = sizeZ / 2
        with Edit(bpy_obj) as edit:
            if topEdgeRing is not None:
                edit.deselectAll()
                for edge in edit.edges:
                    co0 = edge.verts[0].co
                    co1 = edge.verts[1].co
                    if co0.z >= tz and co1.z >= tz:
                        edge.select = True
                edit.bevel(
                    offset=topEdgeRing[0],
                    segments=topEdgeRing[1],
                    offset_type="WIDTH",
                )
            if botEdgeRing is not None:
                edit.deselectAll()
                for edge in edit.edges:
                    co0 = edge.verts[0].co
                    co1 = edge.verts[1].co
                    if co0.z <= -tz and co1.z <= -tz:
                        edge.select = True
                edit.bevel(
                    offset=botEdgeRing[0],
                    segments=botEdgeRing[1],
                    offset_type="WIDTH",
                )
            if sideEdges is not None:
                edit.deselectAll()
                for edge in edit.edges:
                    co0 = edge.verts[0].co
                    co1 = edge.verts[1].co
                    if co0.z != co1.z:
                        edge.select = True
                edit.bevel(
                    offset=sideEdges[0],
                    segments=sideEdges[1],
                    offset_type="WIDTH",
                )
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj

    @staticmethod
    def Trapeze3D(
        topX: TType.UnitOfLength = 0.8,
        topY: TType.UnitOfLength = 0.8,
        botX: TType.UnitOfLength = 1.0,
        botY: TType.UnitOfLength = 1.0,
        sizeZ: TType.UnitOfLength = 1.0,
        material: TType.MaterialParams = None,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
    ):
        topX = TType.UnitOfLength.parse(topX)
        topY = TType.UnitOfLength.parse(topY)
        botX = TType.UnitOfLength.parse(botX)
        botY = TType.UnitOfLength.parse(botY)
        sizeZ = TType.UnitOfLength.parse(sizeZ)
        bpy_obj = Mesh.Rectangle(botX, botY)
        with Edit(bpy_obj) as edit:
            edit.extrude(z=sizeZ)
            edit.ScaleBy(topX / botX, topY / botY)
        Object.TransformTo(bpy_obj, location, rotation, scale)
        if material is not None:
            Material(bpy_obj).update(**material)
        return bpy_obj