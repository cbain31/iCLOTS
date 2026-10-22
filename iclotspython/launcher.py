"""Lazy desktop launcher and headless installation diagnostics."""

import argparse
import importlib.metadata
import json
import platform

from ._version import __version__


def environment_report():
    versions = {}
    for name in ("numpy", "PySide6", "matplotlib", "openpyxl", "opencv-python", "trackpy", "pandas", "scipy", "scikit-image", "scikit-learn"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {"iclots": __version__, "python": platform.python_version(), "platform": platform.platform(), "dependencies": versions}


def main(argv=None):
    parser = argparse.ArgumentParser(description="iCLOTS modern desktop (scientific compatibility preview)")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--check", action="store_true", help="Print installed dependency versions without importing Qt or analysis libraries")
    arguments = parser.parse_args(argv)
    if arguments.check:
        print(json.dumps(environment_report(), indent=2))
        return 0
    try:
        from .gui.application import run
    except ImportError as exc:
        parser.exit(2, f"Desktop dependency unavailable: {exc}. Install this checkout with python -m pip install '.[desktop,analysis]'.\n")
    return run(["iclots"])
