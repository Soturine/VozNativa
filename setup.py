"""Build hook: bundle references/ and assets/ into the wheel.

Metadata lives in pyproject.toml. The skill reads these folders from the
checkout; an installed package reads the bundled copy (voznativa/_bundled),
so `voznativa refs/contract/profile/rewrite` work without a checkout.
"""
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

BUNDLED = ("references", "assets")


class BuildPyWithReferences(build_py):
    def run(self):
        super().run()
        root = Path(__file__).resolve().parent
        target = Path(self.build_lib) / "voznativa" / "_bundled"
        for name in BUNDLED:
            source = root / name
            if source.is_dir():
                shutil.copytree(source, target / name, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildPyWithReferences})
