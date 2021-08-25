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


SYMBOL_TABLE = message_factory.GetMessages(list(_get_file_descriptor_protos()))


def get_prototype(type_name: str) -> message.Message:
  return SYMBOL_TABLE[type_name]
