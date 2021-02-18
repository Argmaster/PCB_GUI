import sys
import os
import re
import json
import pickle
import time

sys.path.append(os.getcwd())
from src.py.bpyx import *
from src.py.pinout import Pinout


SAFETY_HEADER = """
def print(*args, **kwargs):         raise RuntimeError("No IO operation allowed in __gen__ file.")
def input(*args, **kwargs):         raise RuntimeError("No IO operation allowed in __gen__ file.")
def open(*args, **kwargs):          raise RuntimeError("No IO operation allowed in __gen__ file.")
def exec(*args, **kwargs):          raise RuntimeError("No code execution allowed in __gen__ file.")
def eval(*args, **kwargs):          raise RuntimeError("No code evaluation allowed in __gen__ file.")
def __import__(*args, **kwargs):    raise RuntimeError("No import operation allowed in __gen__ file.")
"""

TType.PathExpression.magic_symbols = {
    "$fontdir": f"{os.getcwd()}/data/assets/fonts",
    "$cwd": f"{os.getcwd()}",
    "$default": f"{os.getcwd()}/data/assets/fonts/JetBrainsMono/JetBrainsMono.ttf",
}


class ModelPackage:
    def __init__(self, package_path: str) -> None:
        self.package_path = package_path
        self.dec_path = f"{package_path}/__dec__.json"
        self.prm_path = f"{package_path}/__prm__.json"
        self.bot_path = f"{package_path}/__bot__.png"
        self.top_path = f"{package_path}/__top__.png"
        with open(self.dec_path, "r", encoding="utf-8") as file:
            self.dec_dict = json.load(file)
        self._class = str(self.dec_dict.get("class"))
        self._model = str(self.dec_dict.get("model"))
        self._author = str(self.dec_dict.get("author"))
        self._dscp = str(self.dec_dict.get("dscp"))
        self._other = list(self.dec_dict.get("other"))
        with open(self.prm_path, "r", encoding="utf-8") as file:
            self.prm_dict = json.load(file)

    def params(self):
        return self.prm_dict


class TemplatePackage:
    def __init__(self, package_path: str) -> None:
        self.package_path = package_path
        self.pkg_path = f"{package_path}/__pkg__"
        self.gen_path = f"{package_path}/__gen__"
        self.tem_path = f"{package_path}/__tem__"
        with open(self.pkg_path, "r", encoding="utf-8") as file:
            self.pkg_dict = json.load(file)
        self._class = str(self.pkg_dict.get("class"))
        self._author = str(self.pkg_dict.get("author"))
        self._dscp = str(self.pkg_dict.get("dscp"))
        with open(self.gen_path, "r", encoding="utf-8") as file:
            self.gen_source = file.read()
        with open(self.tem_path, "r", encoding="utf-8") as file:
            self.tem_dict = json.load(file)

    @staticmethod
    def make_safe(source: str) -> str:
        source = re.sub(
            r"from .*? import .*?\n|import .*?\n|import .*? as .*?\n|from .*? import .*? as .*?\n",
            "",
            source,
        )
        # test if no import statements are present in code
        if re.search(r"\s+import\s+", source) is not None:
            raise RuntimeError("Import keyword forbidden in .pyg/.pyt file.")
        # prepend source code with header code overwriting all forbidden functions
        source = SAFETY_HEADER + source
        return source

    def params_json(self):
        return json.dumps(self.tem_dict)

    def execute(self, template_params: dict):
        # clear workspace
        Global.deleteAll()
        exec(
            self.make_safe(self.gen_source),
            {
                "time": time,
                "bpy": bpy,
                "bmesh": bmesh,
                "numpy": numpy,
                "math": math,
                "re": re,
                "json": json,
                "pickle": pickle,
                "Object": Object,
                "TType": TType,
                "Template": Template(self.tem_dict, template_params),
                "Mesh": Mesh,
                "Modifier": Modifier,
                "Material": Material,
                "Transform": Transform,
                "Global": Global,
                "Edit": Edit,
                "LowLevel": LowLevel,
            },
        )


def stdout(mess):
    sys.stdout.write(json.dumps(mess) + "\n")
    sys.stdout.flush()


def stdin():
    return json.loads(sys.stdin.readline())


def getTemplateParams():
    stdout(TemplatePackage(stdin()).params_json())


def genModelFile():
    TemplatePackage(stdin()).execute(ModelPackage(stdin()).params())
    Global.Export(stdin())


def exc():
    stdout("OK")
    time.sleep(0.1)
    exit()


def IO():
    stdout("READY")
    callbacks = {
        "GMF": genModelFile,
        "GTP": getTemplateParams,
        "EXC": exc,
    }
    while True:
        code = stdin()
        if code:
            callbacks[code]()


if __name__ == "__main__":
    # pkg = TemplatePackage("./totht")
    # pkg.execute({})
    # Blender.Object.exportObject("./test.glb")
    IO()
