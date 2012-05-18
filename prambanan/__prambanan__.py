import os

dir = os.path.dirname(os.path.realpath(__file__))
f = lambda n: os.path.join(dir, n)

job_configs = [
        {
        "files": [f("math.py"), f("time.py"), f("datetime.py")],
        "output": f(os.path.join("..", "js")),
        "type_warning": False,
        },
]

configs = [
        {
        "files": [f("."), f("lib")],
        "output": "prambanan.stdlib.js",
        "base_namespace": "",
        },
]
