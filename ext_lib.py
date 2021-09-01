# This library should import all extension protos used by symfs.

from types import ModuleType
from typing import Iterable, Iterator, Optional

import logging

from google.protobuf import message

import ext_pb2

_EXCLUDE_MODULES = {
    'google.protobuf.message',
    'logging',
    'types.ModuleType',
    'typing.Iterable',
    'typing.Iterator',
    'typing.Optional',
}


def _get_modules(
    exclude_modules: Optional[Iterable] = None) -> Iterator[ModuleType]:
  if exclude_modules is None:
    exclude_modules = _EXCLUDE_MODULES
  for module in globals().values():
    if isinstance(module,
                  ModuleType) and module.__name__ not in exclude_modules:
      yield module


def get_prototype(type_name: str) -> message.Message:
  """Get prototype given the name.

  Args:
    type_name: The fully qualified message name (not type_url).

  Raises:
    KeyError: If we cannot find a prototype corresponding to the type_name.

  Returns:
    The prototype that can be used to construct proto messages.
  """
  for module in _get_modules():
    try:
      return getattr(module, '_sym_db').GetSymbol(type_name)
    except KeyError:
      logging.warning('Did not find %s in %s.', type_name, module.__name__)

  raise KeyError(f'Unable to find message {type_name}.')
