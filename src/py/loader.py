import sys
import os
import re
import json
import pickle
import time

sys.path.append(os.getcwd())
from src.py.bpyx import *


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
            compile(self.make_safe(self.gen_source), "<__gen__.source>", "exec"),
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

    def makeBotIcon(self, template_params, path_to_save):
        Global.deleteAll()
        self.execute(template_params)
        bpy_obj = Global.getActive()
        # get current object dimensions
        width, height, z = bpy_obj.dimensions
        # scale it up to be 1
        max_dim = max(width, height)
        scale = 1 / max_dim
        Transform.scale(scale, scale, scale)
        # get new dimensions
        width, height, z = bpy_obj.dimensions
        bbox_md = Object.bboxMaxDist(bpy_obj)
        bpy.ops.object.light_add(
            type="SUN",
        )
        Object.RotateTo(Global.getActive(), y="-180deg")
        camera = Camera(
            location=(bpy_obj.location.x, bpy_obj.location.y, -(1 + z + bbox_md)),
            rotation=(0, "180deg", 0),
        )
        camera.ortho_scale = bbox_md * 2.1
        camera.type = "ORTHO"
        camera.setMain()
        Global.eevee()
        Global.render(f"{path_to_save}/__bot__.png", 1920, 1920)


class stdin:
    code: str
    data: Any

    def __init__(self) -> None:
        line = sys.stdin.readline().strip()
        while not line:
            line = sys.stdin.readline().strip()
        block = json.loads(line)
        self.code = block["code"]
        self.data = block["data"]

    @staticmethod
    def stdout(status: str, trace: str="", data: Any=None) -> None:
        sys.stdout.flush()
        sys.stdout.write(
            json.dumps({"status": status, "trace": trace, "data": data}) + "\n"
        )
        sys.stdout.flush()


class IO:
    IO_in: stdin

    def mainloop(self) -> None:
        stdin.stdout("READY")
        callbacks = {
            "GMF": self.genModelFile,
            "MBI": self.makeBotIcon,
            "GTP": self.getTemplateParams,
            "EXC": self.exc,
        }
        while True:
            try:
                self.IO_in = stdin()
                callbacks[self.IO_in.code](self.IO_in)
            except Exception as e:
                stdin.stdout("ERROR", str(e.args), "")


    def makeBotIcon(self, IO_in: stdin):
        tp = TemplatePackage(IO_in.data["template_path"])
        tp.makeBotIcon(
            IO_in.data["template_params"],
            TType.PathExpression.resolve(IO_in.data["model_path"]),
        )
        IO_in.stdout("OK")

    def getTemplateParams(self, IO_in: stdin):
        IO_in.stdout("OK", "", TemplatePackage(IO_in.data['template_path']).params_json())

    def genModelFile(self, IO_in: stdin):
        TemplatePackage(IO_in.data['template_path']).execute(ModelPackage(stdin()).params())
        Global.Export(IO_in.data['output_path'])
        IO_in.stdout("OK")

    def exc(self, IO_in: stdin):
        IO_in.stdout("OK")
        time.sleep(0.5)
        exit()


if __name__ == "__main__":
    # pkg = TemplatePackage("./totht")
    # pkg.execute({})
    # Blender.Object.exportObject("./test.glb")
    IO().mainloop()
