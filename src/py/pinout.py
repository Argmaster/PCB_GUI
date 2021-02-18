from numpy import linspace
import json
from src.py.PIL import Image, ImageDraw
from src.py.bpyx import TType


class Pinout:
    def __init__(
        self,
        size=1,
        ow=0,
        pw=0,
        ph=0,
        bg="#374f2f",
        c="#f2c42c",
        o="#c7a124",
        style="R",
    ) -> None:
        self.size = size
        self.pw = pw
        self.ph = ph
        self.bg = bg
        self.c = c
        self.ow = ow
        self.o = o
        self.style = style
        self.pins = []

    def __call__(
        self,
        size=1,
        ow=0,
        pw=0,
        ph=0,
        bg="#374f2f",
        c="#f2c42c",
        o="#c7a124",
        style="R",
    ) -> None:
        self.size = size
        self.pw = pw
        self.ph = ph
        self.bg = bg
        self.c = c
        self.ow = ow
        self.o = o
        self.style = style
        self.pins = []

    def pinAt(self, x, y):
        x = TType.UnitOfLength.parse(x)
        y = TType.UnitOfLength.parse(y)
        self.pins.append([x, y])

    def pinArray(self, x, y, dx, dy, count, origin="center"):
        x = TType.UnitOfLength.parse(x)
        y = TType.UnitOfLength.parse(y)
        dx = TType.UnitOfLength.parse(dx)
        dy = TType.UnitOfLength.parse(dy)
        if origin == "center":
            args = (-count / 2, count / 2, count)
        elif origin == "side":
            args = (0, count, count)
        else:
            raise RuntimeError("Invalid origin should be either 'center' or 'side'.")
        for i in linspace(*args):
            self.pins.append([x + dx * i, y + dy * i])

    def dict(self):
        return {
            "size": self.size,
            "bg": self.bg,
            "c": self.c,
            "ow": self.ow,
            "o": self.o,
            "pw": self.pw,
            "ph": self.ph,
            "style": self.style,
            "pins": self.pins,
        }

    def json(self):
        return json.dumps(self.dict(), indent="  ")

    @staticmethod
    def image(pin_data, width=300, height=300):
        img = Image.new(
            "RGBA", (width, height), TType.Color.parseHex(pin_data["bg"], False)
        )
        draw = ImageDraw.ImageDraw(img)
        dpi = width / TType.UnitOfLength.parse(pin_data["size"])
        c = TType.Color.parseHex(pin_data["c"], False)
        ow = int(TType.UnitOfLength.parse(pin_data["ow"]) * dpi)
        o = TType.Color.parseHex(pin_data["o"], False)
        pw = int(TType.UnitOfLength.parse(pin_data["pw"]) * dpi)
        ph = int(TType.UnitOfLength.parse(pin_data["ph"]) * dpi)
        style = pin_data["style"]
        for pin in pin_data["pins"]:
            x = int(TType.UnitOfLength.parse(pin[0]) * dpi + 150 - pw / 2)
            y = int(TType.UnitOfLength.parse(pin[1]) * dpi + 150 - ph / 2)
            if style == "R":
                draw.rectangle([x, y, x + pw, y + ph], c, o, ow)
            elif style == "C":
                draw.ellipse([x, y, x + pw, y + ph], c, o, ow)
        return img
