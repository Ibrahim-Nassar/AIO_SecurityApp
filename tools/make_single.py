from __future__ import annotations

import base64
import io
import os
import shutil
import sys
import tempfile
import zipapp


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "ioc_checker")
DIST_PYZ = os.path.join(ROOT, "ioc_checker.pyz")
SINGLE = os.path.join(ROOT, "IOC_Checker_SINGLE.py")


def build_pyz():
    if os.path.exists(DIST_PYZ):
        os.remove(DIST_PYZ)
    # If package contains __main__.py, omit 'main' parameter per zipapp rules
    has_main = os.path.exists(os.path.join(PKG, "__main__.py"))
    if has_main:
        zipapp.create_archive(PKG, DIST_PYZ)
    else:
        zipapp.create_archive(PKG, DIST_PYZ, main="ioc_checker.app:main")


def build_single():
    with open(DIST_PYZ, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    stub = f"""
import base64, io, zipfile, runpy, sys, tempfile, os
EMBEDDED = b"{b64}"
data = base64.b64decode(EMBEDDED)
tmpdir = tempfile.mkdtemp(prefix="ioc_checker_")
pyz_path = os.path.join(tmpdir, "app.pyz")
with open(pyz_path, "wb") as f:
    f.write(data)
sys.path.insert(0, pyz_path)
runpy.run_module("ioc_checker.app", run_name="__main__")
"""
    with open(SINGLE, "w", encoding="utf-8") as f:
        f.write(stub)


def main():
    build_pyz()
    build_single()
    print("Built:", DIST_PYZ)
    print("Built:", SINGLE)


if __name__ == "__main__":
    main()


