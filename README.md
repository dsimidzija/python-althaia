# Althaia

[![PyPI Version](https://badgen.net/pypi/v/althaia)](https://pypi.org/project/althaia/)
[![License](https://badgen.net/pypi/license/althaia)](https://pypi.org/project/althaia/)
[![PyPI Python](https://badgen.net/pypi/python/althaia)](https://pypi.org/project/althaia/)
[![Downloads](https://pepy.tech/badge/althaia)](https://pepy.tech/project/althaia)

Althaia: _from Latin althaea, from Greek althaia - marsh mallow (literally: healing plant), from Greek althein to heal_

## What is it?

Althaia is a very simple fork of [marshmallow][], with patches to improve the performance when dumping large sets
of data. It is then also compiled via [cython][] for some extra performance boost. Ideally, these patches will
one day find their way into the upstream marshmallow in some cleaner form, and this package will become obsolete.

## How does it work?

During the serialization process, marshmallow repeats a lot of lookup operations for each object it's attempting to
serialize, even though these values never change during the single execution. The main patch in this repo is
basically reading those values once and creating a serializer function, which is much more performant on large
data sets.

The entire thing is then compiled into C extension modules and released only as binary wheels.

Check out the original [upstream PR][] for some discussion, or my [original announcement][dsi-announcement].

## How fast is it?

It really depends on your data and usage, but using the `benchmark.py` test from the upstream marshmallow repo,
Althaia seems to shave off about 56% of execution time on average. These values are an example test run results
from the upstream benchmark:

| Upstream(usec/dump) | Althaia(usec/dump) | Improvement(%) |
|--------------------:|-------------------:|---------------:|
|                8.97 |               3.95 |             56 |
|                8.98 |               3.88 |             56 |
|                9.45 |               4.17 |             56 |
|                9.30 |               3.98 |             57 |

The table is the result of the following commands:

    python performance/benchmark.py
    python performance/benchmark.py --object-count 1000
    python performance/benchmark.py --iterations=5 --repeat=5 --object-count 20000
    python performance/benchmark.py --iterations=10 --repeat=10 --object-count 10000

They are also available in this repo as `poetry run task upstream-performance`. Note that you may get different
results while running the benchmarks (the numbers above were obtained with Althaia v4.3.0, generally speaking you
should be getting better results with newer versions, but sometimes not).

## Installation

```bash
pip install althaia
```

**NOTE**: This is still a work in progress and a wheel may not be available for your platform yet. PRs welcome!

## Usage

There are two ways to use Althaia: as a standalone package, or as a drop-in replacement for marshmallow.
Latter method is the recommended one. Add the following code as early as possible in your app bootstrap:

```python
import althaia
althaia.patch()
```

This will install a Python meta path importer which will mimic marshmallow for the rest of your project, without any
changes to the codebase, i.e. `import marshmallow` will work as expected. If and when this package becomes obsolete,
there will be no need to change the rest of your source to revert to upstream marshmallow.

Alternatively, you can use Althaia directly:

```python
from althaia import marshmallow
# or, e.g.
from althaia.marshmallow import Schema
```

Though I'm not sure why one would do that.

> Obviously, for all _actual_ usage of marshmallow, you should always refer to the excellent [marshmallow docs][].

## Bugs & Contributing

If there are bugs, please make sure they are not upstream marshmallow bugs before reporting them. Since the patches
applied are picking apart some of the marshmallow internals, any breakage should be immediately visible, and the
chances are that most bugs _will_ be upstream bugs.

Contributing [manylinux][] builds for the CI pipeline is most welcome.

**When opening pull requests, please target the `develop` branch by default.**

If you have any other ideas on how to tweak the performance, feel free to contribute in any way you can!

## Versioning & Releases

Althaia will always follow the upstream version of marshmallow to reduce confusion. In other words, Althaia version
`X.Y.Z` will use marshmallow version `X.Y.Z`.

Additionally, if it comes to some changes on Althaia side (repo structure, build process, bugfixes),
PEP440 will be followed and will be released either as alpha, beta, rc (`X.Y.ZaN`, `X.Y.ZbN`, `X.Y.ZrcN`) if there is
still no change in the upstream dependency, or post-releases (`X.Y.ZpostN`). Since bugfixing is discouraged for
post-releases, there may also be a hotfix release as `X.Y.Z.N`, where `N` is the hotfix version.

`dev` releases may appear on test PyPI (`X.Y.Z.devN`), but these are not relevant to the general public.

There will obviously be some delay between marshmallow and Althaia releases, and it is inevitable that I will get
sloppy over time, so feel free to create a GitHub issue if you need an urgent update to latest marshmallow.

## Developing

Althaia is using [Poetry][] with a custom build script, and some [taskipy][] scripts to facilitate things.
You can see them defined in `pyproject.toml`, or just type `poetry run task --list`.

Preparing a new version TL;DR:

* Edit `pyproject.toml` and change the version of the packages for upstream marshmallow and Althaia itself.
* Run `poetry run task version-check`.
* Run `poetry run task build`.
* Run `poetry run task upstream-test`.
* [Optional] Run `poetry run task upstream-performance`.
* [Optional] Inspect the wheel content with `poetry run task inspect`.
* Run `poetry run task publish-test` to deploy to test PyPI.

## Known Issues

* If you have any marshmallow warnings ignored in your `pytest.ini`, i.e. you have `filterwarnings` set up
  to ignore an error starting with `marshmallow.warnings`, you will get an import error even if you're doing
  `althaia.patch()` in your `conftest.py`. As a workaround, you can change it to start with
  `althaia.marshmallow.warnings`. This happens because pytest is trying to import marshmallow before Althaia
  gets a chance to patch the importer.
* Since althaia 3.20.1, the support for python3.7 and 3.8 has been dropped, unlike marshmallow which has dropped
  support only for python3.7. The reason for this are massive changes in typing annotation starting from python3.9,
  which are no longer supported by the recently released Cython 3.0.0. Maintaining patches for 3.8 and 3.9+
  would be difficult without being a significant time sink. Since python3.8 is already in security-updates-only state,
  it's much easier to just drop it.
* **Important:** This fork was created for a specific work project I was maintaining. I am no longer maintaining it, so
  expect the updates to be delayed by a rude amount of time.

[marshmallow]: https://github.com/marshmallow-code/marshmallow
[cython]: https://github.com/cython/cython
[upstream PR]: https://github.com/marshmallow-code/marshmallow/pull/1649
[serialization benchmark]: https://voidfiles.github.io/python-serialization-benchmark/
[serialization-stalled]: https://github.com/voidfiles/python-serialization-benchmark/issues/26
[Toasted Marshmallow]: https://github.com/lyft/toasted-marshmallow
[marshmallow docs]: https://marshmallow.readthedocs.io/en/stable/
[manylinux]: https://github.com/pypa/manylinux
[Poetry]: https://python-poetry.org/
[taskipy]: https://github.com/illBeRoy/taskipy
[dsi-announcement]: http://dsimidzija.github.io/posts/introducing-althaia-speedy-marshmallow-fork/
