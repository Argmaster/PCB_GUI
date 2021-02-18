from abc import abstractmethod, ABC
from typing import Tuple
from src.py.gparser.gconst import Constant


class DrawingBackendAbstract(ABC):
    class DrawingException(Exception):
        pass

    @abstractmethod
    def setDark(self) -> None:
        if self.DEBUG:
            return
        raise NotImplementedError

    @abstractmethod
    def setClear(self) -> None:
        if self.DEBUG:
            return
        raise NotImplementedError

    def setParser(self, parser: object) -> None:
        self.PARSER = parser

    @abstractmethod
    def setSize(
        self,
        width: float,
        height: float,
        originOffsetX: float,
        originOffsetY: float,
    ):
        """Sets size of output image. This method is called by parser

        Args:
            width (float): width of image as coordinates (before conversion)
            height (float): height of image as coordinates (before conversion)
            originOffsetX (float): coordinate coresponding to (0,0) pixel X
            originOffsetY (float): coordinate coresponding to (0,0) pixel Y

        Raises:
            PillowBackend.DrawingException: Raised if heigh or width of image is 0
        """
        if self.DEBUG:
            return
        raise NotImplementedError

    @abstractmethod
    def drawFlash(
        self,
        position: Tuple[float, float],
        brushID: str,
    ) -> None:
        """Draw single brush flash at given position

        Args:
            position (Tuple[float, float]): position (x, y) of center of brush as raw co
            brushID (str): id of a brush in form Dnn
        """
        if self.DEBUG:
            return
        raise NotImplementedError

    @abstractmethod
    def drawLine(
        self,
        begin: tuple,
        end: tuple,
        brushID: str,
        isRegion: bool,
    ) -> None:
        """Draw line with selected brush form begin point
        to end point in previously selected polarity

        Args:
            begin (tuple): (x, y) raw co of begin point
            end (tuple): (x, y) raw co of end point
            brushID (str): id of brush to use
            isRegion (bool): flag specifying wheather line is a boundary of region
        """
        pass

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
        """Draws arc from begin to end with center of arc
        offseted by origin from begin point

        Args:
            begin (tuple): raw begin point coordinate
            end (tuple): raw end point coordinate
            origin (tuple): origin offset
            quadrant (list): quadrant mode
            rotation_direction (list): rotation direction (either CCW or CW)
            brushID (str): Dnn formed brush id string
            isRegion (bool): flag specifying if drawing as region boundary
        """
        pass

    @abstractmethod
    def addTool(
        self,
        identifier: str,
        brushType: str,
        params: list,
    ) -> None:
        """Adds tool object, based on passed arguments, to tool list

        Args:
            identifier (str): Dnn format string identifier
            toolType (str): One of [C, R, O, P]
            param (tuple): shape params (up to 4, automatically dispatched)
        """
        pass

    @abstractmethod
    def finishRegion(
        self,
    ) -> None:
        """
        Called when parser meets G37 (End of region) statement to fill
        region with current fill color
        """
        pass

    @abstractmethod
    def end(self) -> None:
        """Called at the end of parsing gerber file"""
        pass