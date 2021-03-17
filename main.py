import os
import sys

sys.path.append(os.path.dirname(__file__))

from src.py.bpyx import *


m = Mesh.Rectangle(1, 1, 1, (1, 1, 0))
c = Camera()
c.lookAt(m, "180deg", relative_pos=(0, 1, 1))

# %%

from typing import Callable, Any

class A:

    uri: dict={}

    def __init__(self) -> None:
        self.uri['f'](self)
        self.uri['sth'](self)

    class bind:
        def __init__(self, uri: dict) -> None:
            self.uri = uri

        def __call__(self, function: Callable, name: str=None) -> None:
            if name is None:
                name = function.__name__
            self.uri[name] = function

    bind = bind(uri)

    @bind
    def f(self):
        print('hey')

@A.bind
def sth(self):
    print(self)

A()

# %%
