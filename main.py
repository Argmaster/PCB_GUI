import os
import sys

sys.path.append(os.path.dirname(__file__))

from src.py.model import ModelPackage

m = ModelPackage(f"{os.getcwd()}/data/assets/models/3SIP100")
m.make()
args = {
    ''
}
m.shot(top=True)
m.shot(top=False)


# %%
