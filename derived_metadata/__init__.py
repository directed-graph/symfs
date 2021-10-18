"""Load all submodules in this module.

Taken from https://stackoverflow.com/a/3365846/4330447.
"""

import pkgutil

__all__ = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
  if module_name.endswith('_test'):
    continue
  __all__.append(module_name)
  _module = loader.find_module(module_name).load_module(module_name)
  globals()[module_name] = _module
