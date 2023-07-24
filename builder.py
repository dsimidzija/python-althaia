# inspired by:
# https://d39l7znklsxxzt.cloudfront.net/zh/blog/2021/01/19/publishing-a-proprietary-python-package-on-pypi-using-poetry/
import multiprocessing
import os
import platform
import shutil
import subprocess
import sys
import typing
from pathlib import Path

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
    for obj_path in OUTPUT_DIR.rglob("*.rej"):
        obj_path.unlink()


def copy_upstream_source():
    """Stage 2: Copy upstream marshmallow, and change all the import directives.

    This also replaces a lot of the typing annotations which have been deprecated since python3.9,
    and no, I am not proud of how this is done.
    """
    for py_input_path in SOURCE_DIR.rglob("*.py"):
        with open(py_input_path) as py_input_file:
            content = py_input_file.read()

        replace = [
            ("from marshmallow", "from althaia.marshmallow"),
            ("import marshmallow", "from althaia import marshmallow"),
            # these things only work on python39 and above
            # @TODO: create a PR on upstream marshmallow once they drop support for python38.
            ("typing.Dict", "typing.MutableMapping"),
            ("typing.List", "typing.MutableSequence"),
            ("typing.Set", "typing.MutableSet"),
            ("typing.Tuple", "tuple"),
            ("Tuple[", "tuple["),
            ("Dict[", "MutableMapping["),
            (
                "def resolve_hooks(cls) -> dict[types.Tag, list[str]]",
                "def resolve_hooks(cls) -> typing.MutableMapping[types.Tag, typing.MutableSequence[str]]"
            ),
        ]

        for before, after in replace:
            content = content.replace(before, after)

        with open(Path(OUTPUT_DIR, py_input_path.name), "w") as py_output_file:
            py_output_file.write(content)


def apply_patches():
    """Stage 3: Apply our performance patches."""
    try:
        for patch_path in PATCHES_DIR.rglob("*.patch"):
            subprocess.run(
                [
                    "patch",
                    "--strip",
                    "1",
                    "--unified",
                    "--forward",
                    "--input",
                    str(patch_path)
                ],
                check=True,
                capture_output=True,
            )
    except subprocess.CalledProcessError as ex:
        messages = [
            f"Error applying patches: {' '.join(ex.cmd)}",
            f"stderr: {ex.stderr}",
            f"stdout: {ex.stdout}",
        ]
        raise RuntimeError(os.linesep.join(messages)) from ex

    if any(OUTPUT_DIR.rglob("*.rej")):
        raise RuntimeError("Patch(es) not applied properly.")


def cythonize_patched() -> typing.List[Extension]:
    """Stage 4: cythonize all althaia.marshmallow modules."""
    extension_modules: list[Extension] = []

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

    # while the patches themselves bring some minor speedup on PyPy,
    # the compiled modules slow it down enormously
    if platform.python_implementation() != "PyPy":
        distribution = Distribution({
            "ext_modules": cythonize_patched(),
            "cmdclass": {
                "build_ext": cython_build_ext,
            },
        })
        distribution.run_command("build_ext")
        build_ext_cmd = distribution.get_command_obj("build_ext")

        # 2022-06: no idea why build_ext_cmd.copy_extensions_to_source() stopped working suddenly
        for output in build_ext_cmd.get_outputs():
            relative_extension = os.path.relpath(output, build_ext_cmd.build_lib)
            shutil.copyfile(output, relative_extension)
            mode = os.stat(relative_extension).st_mode
            mode |= (mode & 0o444) >> 2
            os.chmod(relative_extension, mode)


if __name__ == "__main__":
    build()
