# This library should import all extension protos used by symfs.

from types import ModuleType
from typing import Any, Callable, Iterable, Iterator, Optional, Union

import pathlib

from absl import logging
from google.protobuf import any_pb2
from google.protobuf import message

try:
  from google.protobuf.pyext.cpp_message import GeneratedProtocolMessageType
except ImportError:
  GeneratedProtocolMessageType = Any
  logging.info(
      'Not using the real GeneratedProtocolMessageType; using Any instead.')

import derived_metadata
import protos.ext_pb2 as ext_pb2
import protos.symfs_pb2 as symfs_pb2

_EXT_PROTO_MODULES = {
    ext_pb2,
}

DerivedMetadataFunction = Callable[[pathlib.Path, any_pb2.Any],
                                   symfs_pb2.Metadata]
DerivedMetadataClass = derived_metadata.abstract_derived_metadata.AbstractDerivedMetadata
Derivation = Union[DerivedMetadataFunction, DerivedMetadataClass]


def get_prototype(
    type_name: str,
    include_modules: Optional[Iterable] = None) -> GeneratedProtocolMessageType:
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


def get_derived_metadata_derivation(name: str) -> Derivation:
  """Get function or class given the name.

  Args:
    name: The fully-qualified name of the function/class (including module(s)).

  Returns:
    A function that takes in a string (file/directory path) and an Any proto or
    a child class of AbstractDerivedMetadata.
  """
  derivation = globals()[name.split('.')[0]]
  for partial_name in name.split('.')[1:]:
    derivation = getattr(derivation, partial_name)

  return derivation
