import importlib
import sys
import warnings
from importlib.metadata import DistributionFinder
from importlib.abc import Loader, MetaPathFinder


class AlthaiaImporter(Loader, MetaPathFinder):
    def __init__(self):
        self._cache = {}

    def find_spec(self, fullname, path, target=None):
        """Only return ModuleSpec if we can handle it.

        We need to exactly match "marshmallow" and startswith("marshmallow.") because we
        otherwise break things for packages such as `marshmallow_utils`.
        """
        if fullname != "marshmallow" and not fullname.startswith("marshmallow."):
            return None

        if fullname not in self._cache:
            self._cache[fullname] = {
                "spec": importlib.machinery.ModuleSpec(fullname, self),
                "module": importlib.import_module(f"althaia.{fullname}"),
            }

        return self._cache[fullname]["spec"]

    def create_module(self, spec):
        if spec.name not in self._cache:
            raise ImportError
        return self._cache[spec.name]["module"]

    def exec_module(self, module):
        """This was already done by importlib.import_module, so just pass to satisfy the Loader ABC."""
        pass

    def find_distributions(self, context=DistributionFinder.Context()):
        """Support breaking change from upstream @ 3.21.0 (2024-02-26).

        Althaia distribution will be handled by the default distribution finder,
        we just need to override marshmallow so we can pretend it's us.
        """
        if context.name != "marshmallow":
            return []

        return [importlib.metadata.Distribution.from_name("althaia")]


def patch():
    if any(isinstance(importer, AlthaiaImporter) for importer in sys.meta_path):
        warnings.warn("Multiple calls to althaia.patch, skipping")
        return
    sys.meta_path.insert(0, AlthaiaImporter())
