import os
import importlib.util
import inspect
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / ".." / "modules"

def find_direct_node_classes():
    for module_dir in MODULES_DIR.iterdir():
        if not module_dir.is_dir():
            continue

        graph_file = module_dir / "graph.py"
        if not graph_file.exists():
            continue

        module_path = f"app.modules.{module_dir.name}.graph"
        spec = importlib.util.spec_from_file_location(module_path, graph_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    name.endswith("Node") and
                    obj.__module__ == module_path  # only directly defined in this file
                ):
                    print(f"from {module_path} import {name}")

if __name__ == "__main__":
    find_direct_node_classes()