from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
import shutil
import subprocess
import sys

if shutil.which("2to3") is None:
    sys.exit("Error: 2to3 is not available. Note: 2to3 is no longer included on Python >=3.13")

class CustomBuild(_build_py):
    def run(self):
        print(">>> Running pre-build patch step using 2to3")
        subprocess.run(["2to3", "--no-diff", "-n", "-w", "./PADS"], check=True)
        print(">>> Applying post2to3.patch")
        subprocess.run(["patch", "-p1", "-i", "./post2to3.patch"], check=False)
        super().run()

setup(cmdclass={"build_py": CustomBuild})
