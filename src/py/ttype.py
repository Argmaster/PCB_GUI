# -*- encoding: utf-8 -*-

import errno
import math
import os
import re
from abc import ABC, abstractmethod
from sys import platform
from typing import Any, Iterable


class Namespace:
    def __init__(self):
        raise RuntimeError(
            "This class is only a namespace, it is not ment to be instantiated."
        )


class TType(Namespace):
    class TType(ABC):
        """Abstract class that implements interface of TType object."""

        def __init__(self, **_) -> None:
            """Sets default value for self._value (holds value of TType)
            if default is None, self._value is set to None,
            otherwise self.set(default) is used to ttype and set default.

            Args:
                default (Any, optional): default value for TType. Defaults to None.
            """
            self._value = None

        def get(self) -> Any:
            """Getter method for TType instance. Returns self._value, but it is
            recommended to acces self._value by this method as it performs
            additional validation.

            Raises:
                TType.NotAValidValue: If value has no default value.

            Returns:
                Any: self._value of this TType
            """
            if self._value == None:
                raise TType.NotAValidValue(
                    "Accessed value was not set to any valid value."
                )
            else:
                return self._value

        @abstractmethod
        def set(self, value) -> None:
            """Abstract method that should implement any validation for this TType

            Args:
                value (Any): value to be set as self._value
            """

        def repr(self):
            return {"ttype": self.__class__.__name__}

    class _Path(ABC):
        """Abstract class for any path-validating object.
        It implements is_pathname_valid for validating path strings
        """

        ERROR_INVALID_NAME = 123

        def is_pathname_valid(self, pathname: str) -> bool:
            """
            `True` if the passed pathname is a valid pathname for the current OS;
            `False` otherwise.
            """
            # invalid if not a string or empty
            try:
                if not isinstance(pathname, str) or not pathname:
                    return False
                drive, pathname = os.path.splitdrive(pathname)
                # Directory guaranteed to exist.
                root_dirname = (
                    os.environ.get("HOMEDRIVE", "C:")
                    if platform == "win32"
                    else os.path.sep
                )
                assert os.path.isdir(root_dirname)  # ...Murphy and her ironclad Law

                # Append a path separator to this directory if needed.
                root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

                # Test whether each path component split from this pathname is valid or
                # not, ignoring non-existent and non-readable path components.
                for pathname_part in pathname.split(os.path.sep):
                    try:
                        os.lstat(root_dirname + pathname_part)
                    # If an OS-specific exception is raised, its error code
                    # indicates whether this pathname is valid or not. Unless this
                    # is the case, this exception implies an ignorable kernel or
                    # filesystem complaint (e.g., path not found or inaccessible).
                    #
                    # Only the following exceptions indicate invalid pathnames:
                    #
                    # * Instances of the Windows-specific "WindowsError" class
                    #   defining the "winerror" attribute whose value is
                    #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
                    #   fine-grained and hence useful than the generic "errno"
                    #   attribute. When a too-long pathname is passed, for example,
                    #   "errno" is "ENOENT" (i.e., no such file or directory) rather
                    #   than "ENAMETOOLONG" (i.e., file name too long).
                    # * Instances of the cross-platform "OSError" class defining the
                    #   generic "errno" attribute whose value is either:
                    #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
                    #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
                    except OSError as exc:
                        if hasattr(exc, "winerror"):
                            if exc.winerror == TType._Path.ERROR_INVALID_NAME:
                                return False
                        elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                            return False
            # If a "TypeError" exception was raised, it almost certainly has the
            # error message "embedded NUL character" indicating an invalid pathname.
            except TypeError as exc:
                return False
            # If no exception was raised, all path components and hence this
            # pathname itself are valid. (Praise be to the curmudgeonly python.)
            else:
                return True

    class ExistingFilePath(TType):
        """TType for paths to file that have to exit at runtime of script."""

        def set(self, value) -> None:
            """Tests if value is a path that leads to existing file
            and if True, sets self._value to value.

            Args:
                value (Any): value to validate and set

            Raises:
                ValueError: Raised if path do not pass validation
            """
            if os.path.isfile(value):
                self._value = value
            else:
                raise ValueError(f"Path {value} is not an existing file.")

    class ExistingDirPath(TType):
        """TType for paths to dictionary that have to exit at runtime of script."""

        def set(self, value) -> None:
            """Tests if value is a path that leads to existing directory
            and if True, sets self._value to value.

            Args:
                value (Any): value to validate and set

            Raises:
                ValueError: Raised if path do not pass validation
            """
            if os.path.isdir(value):
                self._value = value
            else:
                raise ValueError(f"Path {value} is not an existing directory.")

    class PathExpression(TType, _Path):
        """TType for path that requires only syntactic validation"""

        magic_symbols = {}

        @staticmethod
        def resolve(path: str) -> str:
            for symbol, repl in TType.PathExpression.magic_symbols.items():
                path = path.replace(symbol, repl)
            return path

        def set(self, value: str) -> None:
            """Tests if value is path valid for current OS and if True,
            sets self._value to value.

            Args:
                value (Any): value to validate and set

            Raises:
                ValueError: Raised if path do not pass validation
            """
            value = self.resolve(value)

            if self.is_pathname_valid(value):
                self._value = value
            else:
                raise ValueError(f"{value} is not a valid path.")

    class Keyword(TType):
        """TType for validating a value, that can be only one
        of some limited set of values.
        """

        def __init__(self, options, **_) -> None:
            """Checks value that will be set against possible values,
            raises ValueError if it is not there.

            Args:
                default (Any): default value for self._value
            """
            self.options = options
            super().__init__()

        def set(self, value) -> None:
            """Validates given value by checking if it is present in
            self.possible_values if there was any of them. If trere was
            no possible_values list provided, value will never be accepted.

            Args:
                value (Any): Value to be validated and set

            Raises:
                ValueError: Raised if value do not pass validation
            """
            if value not in self.options:
                raise ValueError(
                    f"Value: {value} is not valid, try one of: {self.options}"
                )
            else:
                self._value = value

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "options": self.options,
            }

    class String(TType):
        """This ttype represents just a regular string, performs
        conversion from any type to string before value is set.
        """

        def set(self, value) -> None:
            """Converts value to str and sets it as self._value

            Args:
                value (Any): value to be converted and set
            """
            self._value = str(value)

    class Bool(TType):
        def set(self, value) -> None:
            self._value = bool(value)

    class Int(TType):
        def __init__(self, range, inclusive, **_) -> None:
            self.inclusive = inclusive
            self.range = range
            super().__init__()

        def set(self, value) -> None:
            value = int(value)
            if self.inclusive:
                if self.range[0] < value < self.range[1]:
                    self._value = value
            else:
                if self.range[0] <= value <= self.range[1]:
                    self._value = value

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "range": self.range,
                "inclusive": self.inclusive,
            }

    class Float(TType):
        def __init__(self, range, inclusive, **_) -> None:
            self.inclusive = inclusive
            self.range = list(range)
            super().__init__()

        def set(self, value) -> None:
            value = float(value)
            if isinstance(self.range, tuple):
                if self.range[0] < value < self.range[1]:
                    self._value = value
            else:
                if self.range[0] <= value <= self.range[1]:
                    self._value = value

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "range": self.range,
                "inclusive": self.inclusive,
                "default": self.default,
            }

    class Vector(TType):
        def __init__(self, values, **_) -> None:
            self._value = [TType.TTYPES[val["ttype"]](val) for val in values]

        def set(self, value: Iterable) -> None:
            for i, e in enumerate(value):
                self._value[i].set(e)

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "ttypes": [t.repr() for t in self._value],
            }

    class MaterialParams(TType):
        """
        TType for providing Principled BSDF node configuration.
        material:               object  : None,
        color:                  tuple   : (0.0, 0.0, 0.0, 1.0),
        subsurface:             float   : 0.0,
        subsurfaceRadius:       tuple   : (0.0, 0.0, 0.0, 1.0),
        subsurfaceColor:        tuple   : (0.0, 0.0, 0.0, 1.0),
        metallic:               float   : 0.0,
        specular:               float   : 0.5,
        specularTint:           float   : 0.0,
        roughness:              float   : 1.0,
        anisotropic:            float   : 0.0,
        anisotropicRotation:    float   : 0.0,
        sheen:                  float   : 0.0,
        sheenTint:              float   : 0.5,
        clearcoat:              float   : 0.0,
        clearcoatRoughness:     float   : 0.030,
        IOR:                    float   : 1.450,
        transmission:           float   : 0.0,
        transmissionRoughness:  float   : 0.0,
        emission:               tuple   : (0.0, 0.0, 0.0, 1.0),
        emissionStrength:       float   : 1.0,
        alpha:                  float   : 1.0,
        """

        def __init__(self, params, **_) -> None:
            self._value = {}
            self.set(params)

        def set(self, value: dict) -> None:
            self._value.update(value)

        def __getattr__(self, key) -> Any:
            return self._value[key]

        def __getitem__(self, key) -> Any:
            return self._value[key]

    class NestedTemplate(TType):
        """This TType can be used for nearly infinite nesting of templates."""

        def __init__(self, template: dict, **_) -> None:
            self.__dict__["_kwargs"] = {
                key: TType.TTYPES[val["ttype"]](val) for key, val in template.items()
            }

        def __setattr__(self, key: str, **_) -> None:
            raise RuntimeError(f"Template object can't be modified. <{key}>")

        def __getattr__(self, key: str):
            key = key.lower()
            return self.__dict__["_kwargs"][key].get()

        def get(self):
            return self

        def set(self, kwargs) -> None:
            for key, value in kwargs.items():
                key = key.lower()
                ttype = self.__dict__["_kwargs"][key]
                ttype.set(value)

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "template": {k: v.repr() for k, v in self.__dict__["_kwargs"].items()},
            }

    class Color(TType):
        @staticmethod
        def parseHex(color: str, float_range: bool = True) -> tuple:
            """This function is ment to convert hexadecimal color string into
            tuple of four 0.0-1.0 values (RGBA)

            Args:
                color (str): #nnnnnnnn string where n's are hex values from 0 to F

            Returns:
                list: list of four floats in range 0.0 to 1.0
            """
            color = color.strip()
            if re.match(r"#[0-9A-Fa-f]{8}|#[0-9A-Fa-f]{6}", color) is None:
                raise ValueError("Inalid color format")
            color = color[1:]  # truncate # sign
            color = [
                int(
                    color[index : index + 2],
                    base=16,  # evaluate as hexadecimal value
                )
                for index in range(0, len(color), 2)
            ]
            if len(color) == 3:
                color.append(255)
            return tuple(c for c in color)

        @staticmethod
        def parseRGBA(color: str):
            color = color.strip()
            if not re.match(
                r"rgba\(\s*[0-9]{1, 3}\s*,\s*[0-9]{1, 3}\s*,\s*[0-9]{1, 3}\s*,\s*[0-9]{1, 3}\s*\)",
                color,
            ):
                raise ValueError("Invalid rgba(x,x,x) literal.")
            else:
                color = re.sub(r"rgba\(", "", color)
                color = re.sub(r"\)", "", color).strip()
                color = re.split(r"\s*,\s*", color)
                return tuple(float(x) for x in color)

        @staticmethod
        def parse(value: tuple or list or str or bytes) -> tuple:
            if isinstance(value, (tuple, list)):
                value = list(value)
                if len(value) >= 4:
                    value = value[:4]
                elif len(value) == 3:
                    value.append(255)
                else:
                    raise ValueError(
                        f"Sequence {value} is to short to be threated as color."
                    )
            elif isinstance(value, (str, bytes)):
                if isinstance(value, bytes):
                    value = value.encode("utf-8")
                if re.match(r"\s*#[0-9A-Fa-f]{8}\s*|\s*#[0-9A-Fa-f]{6}\s*", value):
                    value = TType.Color.parseHex(value)
                elif re.match(
                    r"\s*rgba\(\s*[0-9]{1, 3}\s*,\s*[0-9]{1, 3}\s*,\s*[0-9]{1, 3}\s*,\s*[0-9]{1, 3}\s*\)\s*",
                    value,
                ):
                    value = TType.Color.parseRGBA(value)
                else:
                    raise ValueError("Invalid color literal")
            return tuple(round(v / 255, 4) for v in value)

        def set(self, value: tuple or list or str or bytes) -> None:
            self._value = self.parse(value)

        def repr(self):
            return {"ttype": self.__class__.__name__}

    class Angle(TType):
        @staticmethod
        def parse(value) -> float:
            """Converts angle string literal (float+unit) into float
            angle value in radians. Following units are uported:
            deg - degrees
            ' - minutes of arc
            " - seconds of arc
            rad - radians

            Units cannot be mixed.

            Args:
                value (str): string literal to convert

            Returns:
                float: angle in radians
            """
            float_re = r"[\-+]?\d*\.?\d+"
            value = str(value).lower()
            if re.match(f"{float_re}deg$", value):
                return math.radians(float(re.sub(r"deg", "", value)))
            if re.match(f"{float_re}'$", value):
                return math.radians(float(re.sub(r"'", "", value)) * 60)
            if re.match(f'{float_re}"$', value):
                return math.radians(float(re.sub(r'"', "", value)) * 3600)
            elif re.match(f"{float_re}rad$", value):
                return float(re.sub(r"rad", "", value))
            else:
                return float(value)

        def set(self, value: str) -> None:
            self._value = self.parse(value)

    class UnitOfLength(TType):
        @staticmethod
        def parse(value: str) -> float:
            """Function for converting number+unit literals into meters as float

            Args:
                value (str): number+unit literal, accepted unit suffixes are:
                mils, mil   for mils
                in, inch    for inches
                ft          for feets
                mm          for milimeters
                cm          for centimeters
                dm          for decimeters
                m           for meters
                if no suffix matches, literal is treated as usual float

            Units cannot be mixed.
            
            Returns:
                float: converted value
            """
            float_re = r"[\-+]?\d*\.?\d+"
            value = str(value).lower()
            if re.match(f"{float_re}mils$|{float_re}mil$", value):
                return float(re.sub(r"mils|mil", "", value)) * 2.54 * 1e-5
            elif re.match(f"{float_re}inch$|{float_re}in$", value):
                return float(re.sub(r"inch|in", "", value)) * 0.0254
            elif re.match(f"{float_re}ft$", value):
                return float(re.sub(r"ft", "", value)) * 0.3048
            elif re.match(f"{float_re}mm$", value):
                return float(re.sub(r"mm", "", value)) * 0.001
            elif re.match(f"{float_re}cm$", value):
                return float(re.sub(r"cm", "", value)) * 0.01
            elif re.match(f"{float_re}dm$", value):
                return float(re.sub(r"dm", "", value)) * 0.1
            elif re.match(f"{float_re}m$", value):
                return float(re.sub(r"m", "", value))
            else:
                return float(value)

        def set(self, value: str) -> None:
            self._value = self.parse(value)

    TTYPES = {
        "ExistingFilePath": ExistingFilePath,
        "ExistingDirPath": ExistingDirPath,
        "PathExpression": PathExpression,
        "Keyword": Keyword,
        "String": String,
        "Bool": Bool,
        "Int": Int,
        "Float": Float,
        "Vector": Vector,
        "MaterialParams": MaterialParams,
        "NestedTemplate": NestedTemplate,
        "Color": Color,
        "Angle": Angle,
        "UnitOfLength": UnitOfLength,
    }


# $ <>=======================================================<>
# $                    Templating handler
# $ <>=======================================================<>


class Template:
    def __init__(self, template_dict: dict, params: dict) -> None:
        self.__dict__["_kwargs"] = {}
        for key in template_dict.keys():
            param_dict = template_dict[key]
            ttype = TType.TTYPES[param_dict["ttype"]](**param_dict)
            ttype.set(params[key])
            self.__dict__["_kwargs"][key] = ttype
        self.__dict__["definition_lock"] = False

    def __setattr__(self, key: str, *_, **__) -> None:
        raise RuntimeError(f"Template object can't be modified. <{key}>")

    def __getattr__(self, key: str):
        self.__dict__["definition_lock"] = True
        if key not in self.__dict__["_kwargs"]:
            raise KeyError(f"Key {key} was not defined for this template.")
        return self.__dict__["_kwargs"][key].get()
