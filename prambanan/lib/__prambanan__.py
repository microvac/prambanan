import os

dir = os.path.dirname(os.path.realpath(__file__))
f = lambda n: os.path.join(dir, n)

configs = [
    {
        "files": [f("math.py"), f("time.py"), f("datetime.py")],
        "output": f(os.path.join("..", "..", "js", "prambanan.stdlib.js")),
        "type_warning": False,
    },
]

