from __future__ import annotations

from typing import Callable
from src.py.gparser.absbackend import DrawingBackendAbstract
from re import DOTALL, search, compile
from src.py.gparser.gconst import Constant
from queue import Empty, Queue


class Token:
    func: Callable  # function to call
    chunk: str  # matched regex

    def __init__(self, func: Callable, chunk: str) -> None:
        self.func = func
        self.chunk = chunk

    def __call__(self) -> None:
        return self.func(self.chunk)


class GerberParser:
    class ParserException(Exception):
        pass

    class InvalidStateException(ParserException):
        pass

    class ParserMetEOF(ParserException):
        pass

    class GerberSyntaxError(ParserException):
        pass

    class GerberNoMatchSyntax(ParserException):
        pass

    class DeprecatedCommandError(ParserException):
        pass

    class CommandNotImplemented(ParserException):
        pass

    def __init__(
        self,
        drawingBackend: DrawingBackendAbstract,
        verbose: bool = False,
        deprecated: Constant = Constant.IGNORE,
        not_implemented: Constant = Constant.IGNORE,
    ) -> None:
        """GerberParser instance is used for parsing and rendering gerber files
        after initialization by constructor, .parse() method can be used to parse
        gerber file. All the rendering is done via passed to constructor instance of
        DrawingBackednAbstract descendant class.

        Args:
            drawingBackend (DrawingBackendAbstract descendant): instance which is going to
                    be used to render gerber file.
            verbose (bool, optional): specifies wheather parser should print message
                    about each operation performed. Defaults to True.
            deprecated (Constant, optional): constant specifying what to do with
                    deprecated statements that can appear in gerber file. Defaults to Constant.IGNORE.
            not_implemented (Constant, optional): constant specifying what to do with
                    deprecated statements that can appear in gerber file. Defaults to Constant.IGNORE.
        """
        self.ON_NOT_IMPLEMENTED: Constant = not_implemented
        self.ON_DEPRECATED: Constant = deprecated
        self.VERBOSE: bool = verbose
        self.BACKEND = drawingBackend
        self.BACKEND.setParser(self)
        self.CURRENT_X: float = 0
        self.CURRENT_Y: float = 0
        self.STATE_DATA: dict = {}
        self.UNIT: str = "IN"
        self.ACTIVE_TOOL: str = None
        self.DRAWING_MODE: Constant = None
        self.QUADRANT_MODE: Constant = None
        self.IS_REGION_MODE: bool = None
        self.POLARITY: Constant = Constant.DARK
        self.CO_NOTATION: str = None
        self.CF_INT: int = None
        self.CF_FLOAT: int = None
        self.CF_OMIT_ZEROS: bool = None
        self.MACROS: dict = {}
        self._LEFT: float = None
        self._TOP: float = None
        self._RIGHT: float = None
        self._BOT: float = None
        self.TOKEN_STACK: Queue = None
        self.TOKEN_INDEX = 0
        # list of all code blocks that can be caught and handled
        self.SWITCH = [
            # start region mode
            (compile(r"G36"), self.on_G36),
            # end region mode
            (compile(r"G37"), self.on_G37),
            # Select aperture; optionally precedes an aperture selection
            (compile(r"G54"), self.on_Deprecated),
            # Prepare for flash
            (compile(r"G55"), self.on_Comment),
            # quadrant mode to single
            (compile(r"G74"), self.on_G74),
            # quadrant mode to multi
            (compile(r"G75"), self.on_G75),
            # Set the ‘Unit’ to inch
            (compile(r"G70"), self.on_G70),
            # Set the ‘Unit’ to mm
            (compile(r"G71"), self.on_G71),
            # Set the ‘Coordinate format’ to ‘Absolute notation’
            (compile(r"G90"), self.on_G90),
            # Set the ‘Coordinate format’ to ‘Incremental notation’
            (compile(r"G91"), self.on_G91),
            # set linear interpolation
            (compile(r"G01|G1"), self.on_G01),
            # set circular interpolation
            (compile(r"G02|G2"), self.on_G02),
            # set CCW circular interpolation
            (compile(r"G03|G3"), self.on_G03),
            # comment
            (compile(r"G04.*?\*|G4.*?\*", flags=DOTALL), self.on_Comment),
            # coordinate X
            (compile(r"X\d*"), self.on_X),
            # coordinate Y
            (compile(r"Y\d*"), self.on_Y),
            # relative coordinate I
            (compile(r"I\d*"), self.on_I),
            # relative coordinate J
            (compile(r"J\d*"), self.on_J),
            # end of gerber file
            (compile(r"M02|M01|M00"), self.on_M02),
            (compile(r"MIA\dB\d\*%"), self.on_NotImplemented),
            # draw line / arc
            (compile(r"D01\*|D1\*"), self.on_D01),
            # move to position
            (compile(r"D02\*|D2\*"), self.on_D02),
            # draw flash
            (compile(r"D03\*|D3\*"), self.on_D03),
            # load a tool
            (compile(r"D[1-9][0-9]\*"), self.on_DNN),
            # whitespace handling
            (compile(r"\*|\s+"), lambda chunk: None),
            # set polarity to Constant.DARK or Constant.CLEAR
            (compile(r"%LP[CD]\*%"), self.on_LP),
            # set object mirroring
            (compile(r"%LM[XYN]+\*%"), self.on_NotImplemented),
            # set object rotation
            (compile(r"%LR-?\d*\.?\d+\*%"), self.on_NotImplemented),
            # set object scaling
            (compile(r"%LS\d*\.?\d+\*%"), self.on_NotImplemented),
            # Loads a name. Has no effect. It is a comment.
            (compile(r"%LN.*?\*%", flags=DOTALL), self.on_Deprecated),
            # Sets the name of the file image. Has no effect. It is comment.
            (compile(r"%IN.*?\*%", flags=DOTALL), self.on_Deprecated),
            # Add new tool
            (compile(r"%AD.*?\*%", flags=DOTALL), self.on_AD),
            # Add new macro
            (compile(r"%AM.*?\*%", flags=DOTALL), self.on_AM),
            # sets image polarity
            (compile(r"%IP.*?\*%", flags=DOTALL), self.on_Deprecated),
            # AS Sets the ‘Axes correspondence’ graphics state parameter
            # IR Sets ‘Image rotation’ graphics state parameter
            # MI Sets ‘Image mirroring’ graphics state parameter
            # OF Sets ‘Image offset’ graphics state parameter
            # SF Sets ‘Scale factor’ graphics state parameter
            (
                compile(
                    r"%AS.*?\*%|%IR.*?\*%|%MI.*?\*%|%OF.*?\*%|%SF.*?\*%",
                    flags=DOTALL,
                ),
                self.on_NotImplemented,
            ),
            # add block
            (compile(r"%AB.*?\*%.*?%AB\*%", flags=DOTALL), self.on_AM),
            # Sets units to either Inches (IN) or milimeters (MM)
            (compile(r"%MO[IM][NM]\*%"), self.on_MO),
            # sets format of coordinate data
            (compile(r"%FS.*?\*%", flags=DOTALL), self.on_FS),
        ]

    def _parse_co(self, co: str) -> float:
        """Used internally for parsing coordinate data in previously specified
        format stored in CF_INT and CF_FLOAT attributes.

        Args:
            co (str): coordinate coding string

        Returns:
            float: parsed coordinate valie
        """
        CF_LEN = self.CF_INT + self.CF_FLOAT
        if co[0] == "-":
            sing = co[0]
            co = co[1:]
        else:
            sing = ""
        if self.CF_OMIT_ZEROS == "L":
            co = f"{co:0>{CF_LEN}}"
        elif self.CF_OMIT_ZEROS == "T":
            co = f"{co:0>{CF_LEN}}"
        return float(sing + co[: self.CF_INT] + "." + co[self.CF_INT :])

    def tokenize(self, path: str):
        self.TOKEN_STACK = Queue()
        self.TOKEN_STACK_SIZE = 0
        self._CALCULATE_SIZE_MODE = True
        self.CURRENT_X = 0
        self.CURRENT_Y = 0

        with open(path) as file:
            source = file.read().strip()

        cindex = 0
        line_index = 0
        char_index = 0
        slen = len(source)
        size_impact = (self.on_X, self.on_Y, self.on_FS)

        while cindex < slen:
            for regex, func in self.SWITCH:
                chunk = regex.match(source, cindex)
                if chunk is not None:
                    cindex = chunk.end()
                    chunk = chunk.group()
                    if "\n" in chunk:
                        line_index += chunk.count("\n")
                        char_index = len(chunk.split("\n")[1])
                    else:
                        char_index += len(chunk)
                    tk = Token(func, chunk)
                    if tk.func in size_impact:
                        tk()
                    self.TOKEN_STACK_SIZE += 1
                    self.TOKEN_STACK.put(tk)
                    break
            else:
                end_index = cindex + 30 if cindex + 30 < len(source) else len(source)
                raise GerberParser.GerberNoMatchSyntax(
                    f"In line {line_index} no matching token at {char_index} char.\n {source[cindex: end_index]}..."
                )
        self._CALCULATE_SIZE_MODE = False
        self.CURRENT_X = 0
        self.CURRENT_Y = 0

    def feed(self, path: str) -> GerberParser:
        """Feed parser with sorce code from file at given
        path. Source code will be automatically tokenized
        and PCB boundaries will be calculated and set.

        Args:
            path (str): path to gerber file

        Returns:
            GerberParser: self
        """
        try:
            self.tokenize(path)
        except GerberParser.ParserMetEOF:
            pass
        self.BACKEND.setSize(
            self._RIGHT - self._LEFT,
            self._BOT - self._TOP,
            self._LEFT,
            self._TOP,
        )
        return self

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self) -> int:
        if self.TOKEN_STACK is None:
            raise GerberParser.InvalidStateException("Parser was not fed with data.")
        try:
            token = self.TOKEN_STACK.get(block=False)
            token()
            self.TOKEN_INDEX += 1
        except (Empty, GerberParser.ParserMetEOF):
            raise StopIteration()
        return self.TOKEN_INDEX

    def resolve(self) -> None:
        for progress in self:
            pass

    '''def parse(self, path: str) -> DrawingBackendAbstract:
        """This function is main parsing interface and is responsible
        for whole parsing process. "path" argument specifies path to file
        that will be parsed. File have to exist and be valid gerber file.
        Otherwise Exception will be raised.

        Args:
            path (str): path to gerber file

        Constant.RAISEs:
            RuntimeError: Constant.RAISE if parser was not reseted after parsing

        Returns:
            DrawingBackendAbstract: backend with finished render
        """
        if self.line_index:
            raise RuntimeError("Parser needs to be reseted after parsing a file.")
        with open(path) as file:
            source = file.read().strip()
        try:
            self._parse(source, True)
        except GerberParser.ParserMetEOF:
            pass
        self.BACKEND.setSize(
            self._RIGHT - self._LEFT,
            self._BOT - self._TOP,
            self._LEFT,
            self._TOP,
        )
        self.reset()
        try:
            self._parse(source, False)
        except GerberParser.ParserMetEOF:
            pass
        self.BACKEND.end()
        return self.BACKEND'''

    def _updateSize(self, *, x: float = None, y: float = None) -> None:
        """Updates coordinate boundaties of image,
        used while calculating image size before drawing.
        This function is internal, do not call it.

        Args:
            x (float): X coordinate
            y (float): Y coordinate
        """
        if x is not None:
            if self._RIGHT is None:
                self._RIGHT = x
            else:
                self._RIGHT = x if x > self._RIGHT else self._RIGHT
            if self._LEFT is None:
                self._LEFT = x
            else:
                self._LEFT = x if x < self._LEFT else self._LEFT
        if y is not None:
            if self._BOT is None:
                self._BOT = y
            else:
                self._BOT = y if y > self._BOT else self._BOT
            if self._TOP is None:
                self._TOP = y
            else:
                self._TOP = y if y < self._TOP else self._TOP

    def convertToAbsolute(self, x: float = None, y: float = None) -> tuple:
        """Converts passed values from relative to absolute coordinates
        This function have any efect only if self.CO_NOTATION is set to "I"
        (incremental coordinate mode). It returns (x, y) unchanged otherwise

        Args:
            x (float): relative x offset
            y (float): relative y offset

        Returns:
            tuple: (x, y) tuple of converted coordinates
        """
        if self.CO_NOTATION == "I":
            if x is None:
                return self.CURRENT_Y + y
            elif y is None:
                return self.CURRENT_X + x
            else:
                return self.CURRENT_X + x, self.CURRENT_Y + y

        else:
            if x is None:
                return y
            elif y is None:
                return x
            else:
                return x, y

    def on_Deprecated(self, chunk: str) -> None:
        """Called for deprecated functionality/syntax.
        Its effect is specified by self.ON_DEPRECATED value
        set in constructor and can be one of:
            Constant.IGNORE then statement is ignored
            Constant.WARN then warning is printed out
            Constant.RAISE then exception is raised and
                parsing process is terminated

        Args:
            chunk (str): chunk catched by regex coresponding to this function

        Raises:
            GerberParser.DeprecatedCommandError: raised when self.ON_DEPRECATED
                                                is equal to Constant.RAISE
        """
        if self.ON_DEPRECATED == Constant.RAISE:
            raise GerberParser.DeprecatedCommandError(f"In line: {self.line_index + 1}")
        elif self.ON_DEPRECATED == Constant.WARN:
            print(f"Deprecated command in line: {self.line_index + 1}: {chunk}")
        elif self.ON_NOT_IMPLEMENTED == Constant.IGNORE:
            pass
        else:
            raise KeyError(
                f"Invalid self.ON_DEPRECATED value: {self.ON_NOT_IMPLEMENTED}"
            )

    def on_NotImplemented(self, chunk: str) -> None:
        """Called for not implemented functionality/syntax.
        Its effect is specified by self.ON_NOT_IMPLEMENTED value
        set in constructor and can be one of:
            Constant.IGNORE then statement is ignored
            Constant.WARN then warning is printed out
            Constant.RAISE then exception is raised and
                parsing process is terminated

        Args:
            chunk (str): chunk catched by regex coresponding to this function

        Raises:
            GerberParser.DeprecatedCommandError: raised when self.ON_DEPRECATED
                                                is equal to Constant.RAISE
        """
        if self.ON_NOT_IMPLEMENTED == Constant.RAISE:
            raise GerberParser.CommandNotImplemented(
                f"Command not implemented line: {self.line_index}: {chunk}"
            )
        elif self.ON_NOT_IMPLEMENTED == Constant.WARN:
            print(f"Command not implemented line: {self.line_index}: {chunk}")
        elif self.ON_NOT_IMPLEMENTED == Constant.IGNORE:
            pass
        else:
            raise KeyError(
                f"Invalid self.ON_NOT_IMPLEMENTED value: {self.ON_NOT_IMPLEMENTED}"
            )

    def on_G01(self, chunk: str) -> None:
        """This function coresponds to G01 statement which
        sets self.DRAWING_MODE to Constant.LINEAR_INTERPOLATION.

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.DRAWING_MODE = Constant.LINEAR_INTERPOLATION

    def on_G02(self, chunk: str) -> None:
        """This function coresponds to G02 statement which
        sets self.DRAWING_MODE ot Constant.CIRCULAR_CW_INTERPOLATION.

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.DRAWING_MODE = Constant.CIRCULAR_CW_INTERPOLATION

    def on_G03(self, chunk: str) -> None:
        """This function coresponds to G03 statement which
        sets self.DRAWING_MODE to Constant.CIRCULAR_CCW_INTERPOLATION.

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.DRAWING_MODE = Constant.CIRCULAR_CCW_INTERPOLATION

    def on_Comment(self, chunk: str) -> None:
        """This function coresponds to G04/G4 statement which create comment,
        this statement has no effect.

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        pass

    def on_G36(self, chunk: str) -> None:
        """This function coresponds to G36 statement which turns on region
        drawing mode

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.IS_REGION_MODE = Constant.G36
        if self.VERBOSE:
            print("Started drawing region")

    def on_G37(self, chunk: str) -> None:
        """This function coresponds to G37 statement which turns off reguion
        drawing mode and finishes region draw operation

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.IS_REGION_MODE = Constant.G37
        self.BACKEND.finishRegion()
        if self.VERBOSE:
            print("Ended drawing region")

    def on_G54(self, chunk: str) -> None:
        """This function coresponds to deprecated statement responsible for
        selecting aperture, optionally precedes an aperture selection.
        This statement has no effect.

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.on_Deprecated(chunk)

    def on_G70(self, chunk: str) -> None:
        """This function coresponds to deprecated statement responsible
        for seting units to inches. This statemant has an effect,
        sets self.UNIT to "IN"

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.on_Deprecated(chunk)
        self.UNIT = "IN"

    def on_G71(self, chunk: str) -> None:
        """This function coresponds to deprecated statement responsible
        for seting units to milimeters. This statemant has an effect,
        sets self.UNIT to "MM"

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.on_Deprecated(chunk)
        self.UNIT = "MM"

    def on_G74(self, chunk: str) -> None:
        """This function coresponds to G74 statement which sets
        self.QUADRANT_MODE to Constant.SINGLEQUAD

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.QUADRANT_MODE = Constant.SINGLEQUAD

    def on_G75(self, chunk: str) -> None:
        """This function coresponds to G75 statement which sets
        self.QUADRANT_MODE to Constant.MULTIQUAD

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.QUADRANT_MODE = Constant.MULTIQUAD

    def on_G90(self, chunk: str) -> None:
        """This function coresponds to G90 deprecated statement which
        sets coordinate notation to absolute

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.on_Deprecated(chunk)
        self.CO_NOTATION = "A"

    def on_G91(self, chunk: str) -> None:
        """This function coresponds to G91 deprecated statement which
        sets coordinate notation to incremental

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.on_Deprecated(chunk)
        self.CO_NOTATION = "I"

    def on_MO(self, chunk: str) -> None:
        """This function coresponds to MO.. statement which is responsible
        for setting self.UNIT to either "IN" for MOIN or "MM" for MOMM

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.UNIT = chunk[3:5]
        if self.VERBOSE:
            print("Set Unit:", self.UNIT)

    def on_FS(self, chunk: str) -> None:
        """This function corespods to FS statement which is responsible
        for full coordinate format specification including notation and
        precision

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.CF_OMIT_ZEROS = chunk[3]
        self.CO_NOTATION = chunk[4]
        FORMAT = search(r"X\d\d", chunk).group()
        self.CF_INT = int(FORMAT[1])
        self.CF_FLOAT = int(FORMAT[2])
        if self.VERBOSE:
            print(
                "Format:",
                self.CF_OMIT_ZEROS,
                self.CO_NOTATION,
                self.CF_INT,
                self.CF_FLOAT,
            )

    def on_X(self, chunk: str) -> None:
        """This function corespods to X.... statement which is responsible
        for specifying X coordinate value and preceds operations (eg. D01).
        Coordinate parsed by this function is assigned to self.STATE_DATA["X"]

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        if not self._CALCULATE_SIZE_MODE:
            self.STATE_DATA["X"] = self._parse_co(chunk[1:])
        else:
            co = self.convertToAbsolute(x=self._parse_co(chunk[1:]))
            self.CURRENT_X = co
            self._updateSize(x=co)

    def on_Y(self, chunk: str) -> None:
        """This function corespods to Y.... statement which is responsible
        for specifying Y coordinate value and preceds operations (eg. D01).
        Coordinate parsed by this function is assigned to self.STATE_DATA["Y"]

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        if not self._CALCULATE_SIZE_MODE:
            self.STATE_DATA["Y"] = self._parse_co(chunk[1:])
        else:
            co = self.convertToAbsolute(y=self._parse_co(chunk[1:]))
            self.CURRENT_Y = co
            self._updateSize(y=co)

    def on_I(self, chunk: str) -> None:
        """This function corespods to I.... statement which is responsible
        for specifying I coordinate value and preceds operations (eg. D01).
        Coordinate parsed by this function is assigned to self.STATE_DATA["I"]

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.STATE_DATA["I"] = self._parse_co(chunk[1:])

    def on_J(self, chunk: str) -> None:
        """This function corespods to J.... statement which is responsible
        for specifying J coordinate value and preceds operations (eg. D01).
        Coordinate parsed by this function is assigned to self.STATE_DATA["J"]

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.STATE_DATA["J"] = self._parse_co(chunk[1:])

    def on_DNN(self, chunk: str) -> None:
        """This function corespods to Dnn statement which is responsible
        for selecting aperture with given Dnn identifier (nn in range 10 - 99)

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.ACTIVE_TOOL = chunk[:-1]
        if self.VERBOSE:
            print("Set active tool to:", self.ACTIVE_TOOL)

    def on_D01(self, chunk: str) -> None:
        """This function corespods to D01 statement which is responsible
        for drawing line or arc (depending on self.DRAWING_MODE and
        self.QUADRANT_MODE) with currently selected aperture

        Args:
            chunk (str): chunk catched by regex coresponding to this function

        Raises:
            GerberParser.InvalidStateException: raised for invalid quadrant mode
            GerberParser.InvalidStateException: raised for invalid drawing mode
        """
        NewX, NewY = self.convertToAbsolute(
            self.STATE_DATA.get("X", self.CURRENT_X),
            self.STATE_DATA.get("Y", self.CURRENT_Y),
        )
        if self.DRAWING_MODE == Constant.LINEAR_INTERPOLATION:
            self.BACKEND.drawLine(
                [self.CURRENT_X, self.CURRENT_Y],
                [NewX, NewY],
                self.ACTIVE_TOOL,
                self.IS_REGION_MODE,
            )
            if self.VERBOSE:
                print(
                    f"Draw line from: {self.CURRENT_X} {self.CURRENT_Y} to {NewX} {NewY} with {self.ACTIVE_TOOL}"
                )
        elif self.DRAWING_MODE in (
            Constant.CIRCULAR_CW_INTERPOLATION,
            Constant.CIRCULAR_CCW_INTERPOLATION,
        ):
            if self.QUADRANT_MODE not in (Constant.SINGLEQUAD, Constant.MULTIQUAD):
                raise GerberParser.InvalidStateException(
                    "Quadrant mode is not set to valid value ({self.DRAWING_MODE})"
                )
            self.BACKEND.drawArc(
                [self.CURRENT_X, self.CURRENT_Y],
                [NewX, NewY],
                [
                    self.STATE_DATA.get("I"),
                    self.STATE_DATA.get("J"),
                ],
                self.QUADRANT_MODE,
                self.DRAWING_MODE,
                self.ACTIVE_TOOL,
                self.IS_REGION_MODE,
            )
            if self.VERBOSE:
                print(
                    f"Draw arc from: {self.CURRENT_X} {self.CURRENT_Y} to {NewX} {NewY} with {self.ACTIVE_TOOL}"
                )
        else:
            raise GerberParser.InvalidStateException(
                f"Drawing mode is not set to valid value ({self.DRAWING_MODE})"
            )
        self.CURRENT_X = NewX
        self.CURRENT_Y = NewY
        self.STATE_DATA.clear()

    def on_D02(self, chunk: str) -> None:
        """This function corespods to D02 statement which is responsible for
        moving to different location specified with self.STATE_DATA['X'] and
        self.STATE_DATA['Y'].

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        NewX, NewY = self.convertToAbsolute(
            self.STATE_DATA.get("X", self.CURRENT_X),
            self.STATE_DATA.get("Y", self.CURRENT_Y),
        )
        self.CURRENT_X = NewX
        self.CURRENT_Y = NewY
        self.STATE_DATA.clear()
        if self.VERBOSE:
            print("Moved to:", self.CURRENT_X, self.CURRENT_Y)

    def on_D03(self, chunk: str) -> None:
        """This function corespods to D03 statement which is responsible for
        drawing flash at current location or at location specified by
        self.STATE_DATA['X'] and self.STATE_DATA['Y'].

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        NewX, NewY = self.convertToAbsolute(
            self.STATE_DATA.get("X", self.CURRENT_X),
            self.STATE_DATA.get("Y", self.CURRENT_Y),
        )
        self.STATE_DATA.clear()
        self.BACKEND.drawFlash((NewX, NewY), self.ACTIVE_TOOL)
        self.CURRENT_X = NewX
        self.CURRENT_Y = NewY
        if self.VERBOSE:
            print(f"Flash at {self.CURRENT_X} {self.CURRENT_Y} with {self.ACTIVE_TOOL}")

    def on_M02(self, chunk: str) -> None:
        """This function corespods to M02 statement which implies end of gerber file

        Args:
            chunk (str): chunk catched by regex coresponding to this function

        Raises:
            GerberParser.ParserMetEOF: raised to inform parser that it reached eof
        """
        raise GerberParser.ParserMetEOF

    def on_AD(self, chunk: str) -> None:
        """This function corespods to %ADD.*% statement which is used for adding
        new apertures created from macros and base shapes

        Args:
            chunk (str): chunk catched by regex coresponding to this function

        Raises:
            GerberParser.GerberSyntaxError: raised for invalid brush type
            GerberParser.GerberSyntaxError: raised for invalid brush params
            GerberParser.GerberSyntaxError: raised for repeated brush id
        """
        identifier = chunk[3:6]
        brushType = chunk[6]
        params = chunk[8:-2]
        if brushType not in [
            Constant.BRUSH_RECTANGLE,
            Constant.BRUSH_CIRCLE,
            Constant.BRUSH_OBROUND,
            Constant.BRUSH_POLYGON,
        ]:
            raise GerberParser.GerberSyntaxError(
                f"Invalid brush type in line: {self.line_index}: {brushType}"
            )
        try:
            params = [float(x) for x in params.split("X")]
            params += [0] * (4 - len(params))
        except ValueError:
            raise GerberParser.GerberSyntaxError(
                f"Invalid brush params in line: {self.line_index}: {params}"
            )
        self.BACKEND.addTool(identifier, brushType, params)
        if self.VERBOSE:
            print("Tool:", identifier, brushType, params)

    def on_AM(self, chunk: str) -> None:
        """This function corespods to %AM.*% statement which is used for adding
        new macros. It is not implemented yet.

        Args:
            chunk (str): chunk catched by regex coresponding to this function
        """
        self.on_NotImplemented(chunk)
        if self.VERBOSE:
            print("Macro ->", chunk)

    def on_LP(self, chunk: str) -> None:
        """This function corespods to %LP.% statement which is used for
        selecting either dark (LPD) or clear (LPC) polarity for active aperture

        Args:
            chunk (str): chunk catched by regex coresponding to this function

        Raises:
            GerberParser.GerberSyntaxError: raised if invalid polarity value is given
        """
        if chunk[3] == "D":
            self.POLARITY = Constant.DARK
            self.BACKEND.setDark()
        elif chunk[3] == "C":
            self.POLARITY = Constant.CLEAR
            self.BACKEND.setClear()
        else:
            raise GerberParser.GerberSyntaxError(
                f"Invalid polarity in line: {self.line_index}: {chunk[3]}"
            )
        if self.VERBOSE:
            print("Polarity:", self.POLARITY)
