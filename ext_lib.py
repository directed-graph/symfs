# This library should import all extension protos used by symfs.

from types import ModuleType
from typing import Iterable, Iterator, Optional

import logging

from google.protobuf import message

import ext_pb2

_EXT_PROTO_MODULES = {
    ext_pb2,
}


def get_prototype(
    type_name: str,
    include_modules: Optional[Iterable] = None) -> message.Message:
  """Get prototype given the name.

  Args:
    type_name: The fully qualified message name (not type_url).
    include_modules: An iterable of modules to search for type.

  Raises:
    KeyError: If we cannot find a prototype corresponding to the type_name.

  Returns:
    The prototype that can be used to construct proto messages.
  """
  if include_modules is None:
    include_modules = _EXT_PROTO_MODULES
  for module in include_modules:
    try:
      return getattr(module, '_sym_db').GetSymbol(type_name)
    except KeyError:
      logging.warning('Did not find %s in %s.', type_name, module.__name__)

  raise KeyError(f'Unable to find message {type_name}.')
