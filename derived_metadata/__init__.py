"""Load all submodules in this module.

Taken from https://stackoverflow.com/a/3365846/4330447.
"""

import importlib
import pkgutil

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
  if module_name.endswith('_test'):
    continue
  __all__.append(module_name)
  _module = importlib.import_module(f'.{module_name}', 'derived_metadata')
  globals()[module_name] = _module
