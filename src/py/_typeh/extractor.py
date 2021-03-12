# -*- encoding: utf-8 -*-
import bpy
import inspect
import os


def _extract_req(obj, known_types):
    out = "\n"
    try:
        _otn = obj.__name__
    except:
        _otn = obj.__class__.__name__
    known_types[_otn] = _otn
    print("class", _otn)
    out += f"class {_otn}:\n"
    for prop_name in dir(obj):
        try:
            o_prop = eval(f"o.{prop_name}", {"o": obj})
            if not callable(o_prop):
                _type = type(o_prop)
                _tn = _type.__name__
                if _tn not in known_types:
                    print("prop", _tn)
                    cls = _extract_req(_type, known_types)
                    out = cls + "\n\n" + out
                out += f"    {prop_name}: {known_types[_tn]}\n"
            else:
                if not inspect.isbuiltin(o_prop):
                    try:
                        _signature = inspect.signature(o_prop)
                    except Exception:
                        try:
                            _type = o_prop()
                            _tn = _type.__name__
                            if _tn not in known_types:
                                print("func", _tn)
                                cls = _extract_req(_type, known_types)
                                out = cls + "\n\n\n" + out
                            _signature = f"(*args, **kwargs) -> {known_types[_tn]}"
                        except Exception:
                            _type = "Any"
                            _signature = f"(*args, **kwargs) -> Any"
                out += f"    def {prop_name}{_signature}: ...\n"
        except Exception:
            out += f"    {prop_name}: Any\n"
    return out


def _extract(
    obj,
    known_types={
        "str": "str",
        "int": "int",
        "float": "float",
        "dict": "Dict",
        "list": "List",
        "tuple": "Tuple",
        "type": "type",
        "set": "Set",
        "Any": "Any",
        "NoneType": "None",
        "bool": "bool",
        "builtin_function_or_method": "Union[BuiltinFunctionType, BuiltinMethodType]",
        "method-wrapper": "MethodWrapperType",
        "method": "MethodType",
        "getset_descriptor": "GetSetDescriptorType",
    },
):
    with open(f"{os.getcwd()}/bpy_type_.py", "w") as file:
        file.write("# -*- encoding: utf-8 -*-\n")
        file.write("from __future__ import annotations\n")
        file.write("from types import *\n")
        file.write("from typing import *\n")
        file.write("from _typeshed import *\n")
        file.write(_extract_req(obj, known_types))


# import bmesh

# extract(bpy.context.active_object)
# bpy.ops.object.mode_set(mode="EDIT")
# print(_extract(bmesh.from_edit_mesh(bpy.context.active_object.data)))
# print(_extract(bmesh))
