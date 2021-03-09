import json


class ModelPackage:
    def __init__(self, package_path: str) -> None:
        self.package_path = package_path
        self.dec_path = f"{package_path}/__dec__.json"
        self.bot_path = f"{package_path}/__bot__.png"
        self.top_path = f"{package_path}/__top__.png"
        self.ico_path = f"{package_path}/__ico__.png"
        self.mod_path = f"{package_path}/__mod__.glb"
        with open(self.dec_path, "r", encoding="utf-8") as file:
            self.dec_dict = json.load(file)
        self._class = str(self.dec_dict.get("class"))
        self._model = str(self.dec_dict.get("model"))
        self._author = str(self.dec_dict.get("author"))
        self._dscp = str(self.dec_dict.get("dscp"))
        self._other = list(self.dec_dict.get("other"))
        self.prm_dict = self.dec_dict.get("prm_dict")

    def params(self):
        return self.prm_dict