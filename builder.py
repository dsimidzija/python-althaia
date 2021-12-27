# inspired by:
# https://d39l7znklsxxzt.cloudfront.net/zh/blog/2021/01/19/publishing-a-proprietary-python-package-on-pypi-using-poetry/
import multiprocessing
import os
import platform
import subprocess
from pathlib import Path
from typing import List

from setuptools import Extension, Distribution

from Cython.Build import cythonize
from Cython.Distutils.build_ext import new_build_ext as cython_build_ext

SOURCE_DIR = Path("upstream/src/marshmallow/")
BUILD_DIR = Path("build")
PATCHES_DIR = Path("patches")
OUTPUT_DIR = Path("althaia/marshmallow/")


def clean_build():
    """Stage 1: Remove compiled modules from `althaia/marshmallow`.

    This is necessary because the pipeline which compiles the wheels includes all the compiled
    modules it finds, and for each successive build it includes all the binaries from previous versions.
    """
    for obj_path in OUTPUT_DIR.rglob("*.so"):
        obj_path.unlink()
    for obj_path in OUTPUT_DIR.rglob("*.pyd"):
        obj_path.unlink()


def copy_upstream_source():
    """Stage 2: Copy upstream marshmallow, and change all the import directives."""
    for py_input_path in SOURCE_DIR.rglob("*.py"):
        with open(py_input_path) as py_input_file:
            content = py_input_file.read()

        content = content.replace("from marshmallow", "from althaia.marshmallow")
        content = content.replace("import marshmallow", "from althaia import marshmallow")

        with open(Path(OUTPUT_DIR, py_input_path.name), "w") as py_output_file:
            py_output_file.write(content)


def apply_patches():
    """Stage 3: Apply our performance patches."""
    for patch_path in PATCHES_DIR.rglob("*.patch"):
        subprocess.run(
            [
                "patch",
                "--strip",
                "1",
                "--forward",
                "--input",
                str(patch_path)
            ],
            capture_output=True,
        )


def cythonize_patched() -> List[Extension]:
    """Stage 4: cythonize all althaia.marshmallow modules."""
    extension_modules: List[Extension] = []

    for py_file in OUTPUT_DIR.rglob("*.py"):
        # skip __init__.py on windows, as it causes a weird linking error:
        # https://github.com/cython/cython/issues/2968
        if platform.system() == "Windows" and "__init__" in str(py_file):
            continue
        module_path = py_file.with_suffix("")
        module_path = str(module_path).replace(os.sep, ".")
        extension_module = Extension(
            name=module_path,
            sources=[str(py_file)],
            extra_compile_args=["-O3"],
        )
        extension_modules.append(extension_module)

    return cythonize(
        module_list=extension_modules,
        build_dir=BUILD_DIR,
        annotate=False,
        nthreads=multiprocessing.cpu_count() * 2,
        compiler_directives={"language_level": "3"},
        force=False,
        verbose=5,
    )


def build():
    # if source dir doesn't exist, this is a sdist build and patches are already applied
    # otherwise, we're in dev mode
    if SOURCE_DIR.exists():
        clean_build()
        copy_upstream_source()
        apply_patches()
    distribution = Distribution({
        "ext_modules": cythonize_patched(),
        "cmdclass": {
            "build_ext": cython_build_ext,
        },
    })
    distribution.run_command("build_ext")
    build_ext_cmd = distribution.get_command_obj("build_ext")
    build_ext_cmd.copy_extensions_to_source()


if __name__ == "__main__":
    build()
