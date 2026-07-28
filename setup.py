import os
import sys
import platform
import subprocess
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext


class BuildExtCustom(build_ext):
    def build_extension(self, ext):
        try:
            super().build_extension(ext)
            return
        except Exception as e:
            print(f"Standard setuptools build_ext failed ({e}). Attempting fallback build using Zig...")

        ext_path = self.get_ext_fullpath(ext.name)
        os.makedirs(os.path.dirname(ext_path), exist_ok=True)

        header_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "twell.h"))
        c_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "twell", "twell.c"))

        target_src = c_src_path if os.path.exists(c_src_path) else header_path
        cmd = [
            "zig", "cc", "-shared", "-O2",
            "-DTWELL_IMPL", "-DTWELL_BUILD_DLL",
            target_src,
            "-o", ext_path
        ]
        if target_src == header_path:
            cmd.insert(-2, "-x")
            cmd.insert(-2, "c")

        subprocess.run(cmd, check=True)


ext_modules = [
    Extension(
        "twell._twell",
        sources=["twell/twell.c"],
        include_dirs=["."],
        define_macros=[("TWELL_IMPL", "1"), ("TWELL_BUILD_DLL", "1")],
        extra_compile_args=["/O2"] if platform.system() == "Windows" else ["-O2"],
    )
]

setup(
    packages=find_packages(),
    ext_modules=ext_modules,
    cmdclass={"build_ext": BuildExtCustom},
    package_data={"twell": ["*.dll", "*.so", "*.dylib", "*.pyd", "py.typed", "twell.h", "twell.c"]},
    include_package_data=True,
)
