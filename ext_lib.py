# This library should import all extension protos used by symfs.

from types import ModuleType
from typing import Iterable, Iterator, Optional

import logging
import sys

from google.protobuf import descriptor_pb2
from google.protobuf import message
from google.protobuf import message_factory

import ext_pb2

_EXCLUDE_MODULES = {
    'google.protobuf.descriptor_pb2',
    'google.protobuf.message',
    'google.protobuf.message_factory',
    'logging',
    'sys',
    'types.ModuleType',
    'typing.Iterable',
    'typing.Iterator',
    'typing.Optional',
}
SYMBOL_TABLE = None


def _get_modules(
    exclude_modules: Optional[Iterable] = None) -> Iterator[ModuleType]:
  if exclude_modules is None:
    exclude_modules = _EXCLUDE_MODULES
  for module in globals().values():
    if isinstance(module,
                  ModuleType) and module.__name__ not in exclude_modules:
      yield module


def _get_file_descriptor_protos(
    exclude_modules: Optional[Iterable] = None
) -> Iterator[descriptor_pb2.FileDescriptorProto]:
  for module in _get_modules(exclude_modules):
    descriptor = descriptor_pb2.FileDescriptorProto()
    module.DESCRIPTOR.CopyToProto(descriptor)
    yield descriptor


def get_prototype(type_name: str,
                  self_managed: bool = False) -> message.Message:
  """Get prototype given the name.

  We have a `self_managed` option, because the symbol database of the built
  libraries are, in theory, private variables.

  Args:
    type_name: The fully qualified message name (not type_url).
    self_managed: If set, we will locally generate the desired prototypes.

  Raises:
    KeyError: If we cannot find a prototype corresponding to the type_name.

  Returns:
    The prototype that can be used to construct proto messages.
  """
  if self_managed:
    global SYMBOL_TABLE
    if SYMBOL_TABLE is None:
      SYMBOL_TABLE = message_factory.GetMessages(
          list(_get_file_descriptor_protos()))
    return SYMBOL_TABLE[type_name]

  for module in _get_modules():
    try:
      return getattr(module, '_sym_db').GetSymbol(type_name)
    except KeyError:
      logging.warning('Did not find %s in %s.', type_name, module.__name__)

  raise KeyError(f'Unable to find message {type_name}.')
