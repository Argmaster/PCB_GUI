# -*- encoding: utf-8 -*-

import errno
import math
import os
import re
from abc import ABC, abstractmethod
from sys import platform
from typing import Any, Iterable, List

import numpy


class Namespace:
    def __init__(self):
        raise RuntimeError(
            "This class is only a namespace, it is not ment to be instantiated."
        )


class TType(Namespace):
    _float_regex = "[\\-+]?[0-9]*\\.?[0-9]+"
    _angle_regex = [
        [re.compile(f"{_float_regex}rad"), "rad", 1],
        [re.compile(f"{_float_regex}deg"), "deg", math.pi / 180],
        [re.compile(f"{_float_regex}°"), "°", math.pi / 180],
        [re.compile(f"{_float_regex}'"), "'", math.pi / 10800],
        [re.compile(f'{_float_regex}"'), '"', math.pi / 648000],
        [re.compile(f"{_float_regex}turn"), "turn", math.pi],
        [re.compile(f"{_float_regex}"), "", 1],
    ]
    _unitoflength_regex = [
        [re.compile(f"{_float_regex}mil"), "mil", 2.54 * 1e-5],
        [re.compile(f"{_float_regex}in"), "in", 0.0254],
        [re.compile(f"{_float_regex}ft"), "ft", 0.3048],
        [re.compile(f"{_float_regex}mm"), "mm", 0.001],
        [re.compile(f"{_float_regex}cm"), "cm", 0.01],
        [re.compile(f"{_float_regex}dm"), "dm", 0.1],
        [re.compile(f"{_float_regex}m"), "m", 1],
        [re.compile(f"{_float_regex}"), "", 1],
    ]

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

        @staticmethod
        def _destruct_literal(
            literal: str, literal_regex: List[List[str]]
        ) -> float:
            """Parse given literal by looping over given
            regex list untill length of literal is 0 or no
            match was found.

            Args:
                literal (str): literal to covert
                literal_regex (list): list of regexes

            Returns:
                float: value
            """
            value = 0
            literal = literal.strip()
            while literal:
                literal = literal.strip()
                for regex, repl, multiplier in literal_regex:
                    regex_match = regex.match(literal)
                    if regex_match is not None:
                        literal_match = regex_match.group()
                        literal = literal[regex_match.end() :]
                        literal_match = float(literal_match.replace(repl, ""))
                        value += literal_match * multiplier
                        break
                else:
                    raise SyntaxError(
                        f"Invalid literal '{literal}' no matching syntax."
                    )
            return value

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
        def __init__(self, range, **_) -> None:
            self.range = range
            super().__init__()

        def set(self, value) -> None:
            value = int(value)
            if self.range[0] <= value <= self.range[1]:
                self._value = value
            else:
                raise ValueError(
                    f"Value {value} out of range [{self.range[0]}, {self.range[1]}]"
                )

        def repr(self):
            return {"ttype": self.__class__.__name__, "range": self.range}

    class Float(TType):
        def __init__(self, range, **_) -> None:
            self.range = range
            super().__init__()

        def set(self, value) -> None:
            value = float(value)
            if self.range[0] <= value <= self.range[1]:
                self._value = value
            else:
                raise ValueError(
                    f"Value {value} out of range [{self.range[0]}, {self.range[1]}]"
                )

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "range": self.range,
            }

    class Vector(TType):
        def __init__(self, template, **_) -> None:
            self._value = [TType.TTYPES[val["ttype"]](val) for val in template]

        def set(self, value: Iterable) -> None:
            for i, e in enumerate(value):
                self._value[i].set(e)

        def repr(self):
            return {
                "ttype": self.__class__.__name__,
                "template": [t.repr() for t in self._value],
            }

    class MaterialParams(TType):
        """
        TType for providing Principled BSDF node configuration.
        material:               object  : None,
        color:                  tuple   : TType.Color,
        subsurface:             float   : 0.0,
        subsurfaceRadius:       tuple   : TType.Color,
        subsurfaceColor:        tuple   : TType.Color,
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
        emission:               tuple   : TType.Color,
        emissionStrength:       float   : 1.0,
        alpha:                  float   : 1.0,
        """

        def __init__(self, **_) -> None:
            self._value = {}

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
        def _color_rgb(literal: str) -> list:
            """
            Convert rgba(R, G, B) color literal to number[4] array, alpha 255
            @param {string} literal to parse
            @returns {number[4]} array of 4 numbers in range 0 - 255
            @type {number[4]}
            """
            literal = re.sub(r"\)", "", re.sub(r"rgb\(", "", literal)).split(",")
            literal = [numpy.clip([int(e)], 0, 255)[0] for e in literal]
            literal.append(255)
            return literal

        @staticmethod
        def _color_rgba(literal: str) -> list:
            """
            Convert rgba(R, G, B, A) color literal to number[4] array
            @param {string} literal to parse
            @returns {number[4]} array of 4 numbers in range 0 - 255
            @type {number[4]}
            """
            literal = re.sub(r"\)", "", re.sub(r"rgba\(", "", literal)).split(",")
            literal = [numpy.clip([int(e)], 0, 255)[0] for e in literal]
            return literal

        @staticmethod
        def _number_rgba(_number: int) -> list:
            """
            Convert number 0x0 - 0xFFFFFFFF to array RGBA {number[4]}
            @param {number} _number to parse
            @returns {number[4]} array of 4 numbers in range 0 - 255
            @type {number[4]}
            """
            value = [0, 0, 0, 255]
            i = 0
            while i < 4:
                value[3 - i] = _number % 256
                _number = math.floor(_number / 256)
                i += 1
            return value

        @staticmethod
        def _parse(literal: str) -> list:
            """
            Parse a color literal in one of following forms:
            number:
                0x0 - 0xFFFFFFFF as RRGGBBAA
            string:
                "0xFFFFFFFF" - "0x00000000" RRGGBBAA
                "#FFFFFFFF" - "#00000000"   RRGGBBAA
                "0xFFFFFF" - "0x000000"     RRGGBB alpha 255
                "#FFFFFF" - "#000000"       RRGGBB alpha 255
                "0xFFFF" - "0x0000"         RGBA, -> #ABCD = #AABBCCDD
                "#FFFF" - "#0000"           RGBA, as above
                "0xFFF" - "0x000"           RGB alpha 255 -> #ABC = #AABBCC
                "#FFF" - "#000"             RGB alpha 255, as above
                "rgba(255, 255, 255, 255)" - "rgb(0, 0, 0, 0)"  RGBA
                "rgb(255, 255, 255)" - "rgb(0, 0, 0)"           RGB alpha 255

            @param {string|number} literal literal to resolve
            @returns {number[4]} color array [R, G, B, A]
            @type {number[4]}
            @type {None} if value cannot be parsed
            """
            # parse string literals
            if type(literal) == str:
                # rgb(R, G, B) literal
                if re.match(
                    r"rgb\(\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*\)",
                    literal,
                ):
                    return TType.Color._color_rgb(literal)
                # rgba(R, G, B, A) literal
                elif re.match(
                    r"rgba\(\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*\)",
                    literal,
                ):
                    return TType.Color._color_rgba(literal)
                # 0xFFFFFFFF or #FFFFFFFF literal
                elif re.match(r"[#(0x)][0-9A-Fa-f]{8}", literal):
                    return TType.Color._number_rgba(
                        int(literal.replace("#", "0x"), base=16)
                    )
                # 0xFFFFFF or #FFFFFF literal
                elif re.match(r"[#(0x)][0-9A-Fa-f]{6}", literal):
                    return TType.Color._number_rgba(
                        int((literal + "FF").replace("#", "0x"), base=16)
                    )
                elif re.match(r"[#(0x)][0-9A-Fa-f]{4}", literal):
                    # 0xFFFF or #FFFF literal
                    literal = re.sub(r"#|0x", "", literal)
                    return [
                        int(f"0x{literal[i]}{literal[i]}", base=16) for i in range(4)
                    ]
                elif re.match(r"[#(0x)][0-9A-Fa-f]{3}", literal):
                    # 0xFFF or #FFF literal
                    literal = re.sub(r"#|0x", "", literal)
                    return [
                        int(f"0x{literal[i]}{literal[i]}", base=16) for i in range(3)
                    ] + [255]
            elif type(literal) in (int, float):
                # number literal, values 0 - 4294967295 0x0 - 0xFFFFFFFF
                return TType.Color._number_rgba(int(literal))
            raise SyntaxError(
                f"Invalid literal for Color '{literal}' no matching syntax."
            )

        @staticmethod
        def parse(literal: str) -> tuple:
            return tuple([val / 255 for val in TType.Color._parse(literal)])

        def set(self, value: tuple or list or str or bytes) -> None:
            self._value = self.parse(value)

        def repr(self):
            return {"ttype": self.__class__.__name__}

    class Angle(TType):
        @staticmethod
        def parse(literal: str) -> float:
            """Converts angle literal(s) into single value as radians
            Supported units are listed in TType._angle_regex.

            Units can be mixed, separated by whitespace or not at all.

            Args:
                value (str): string literal to convert

            Returns:
                float: sum of converted values in radians
            """
            if type(literal) == str:
                return TType.TType._destruct_literal(literal, TType._angle_regex)
            else:
                return float(literal)

        def set(self, value: str) -> None:
            self._value = self.parse(value)

    class UnitOfLength(TType):
        @staticmethod
        def parse(literal: str) -> float:
            """Function for converting number+unit literals into meters as float.

            Args:
                value (str): number+unit literal, accepted unit suffixes are:
                mil         for mils
                in          for inches
                ft          for feets
                mm          for milimeters
                cm          for centimeters
                dm          for decimeters
                m           for meters
                if no suffix matches, literal is treated as usual float

            Units can be mixed, separated by whitespace or not at all.

            Returns:
                float: sum of converted values in meters
            """
            if type(literal) == str:
                return TType.TType._destruct_literal(literal, TType._unitoflength_regex)
            else:
                return float(literal)

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
