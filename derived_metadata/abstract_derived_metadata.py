from typing import Any, Optional

import abc
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

import protos.symfs_pb2 as symfs_pb2


class AbstractDerivedMetadata(abc.ABC):
  """Class to hold state for generating symfs_pb2.Metadata.

  Attributes:
    ParametersType: The type expected to be unpacked from the optional
      `parameters` Any proto. Child classes need to override this to use.
  """

  # Child classes should override with expected `parameters` type.
  ParametersType: Optional[GeneratedProtocolMessageType] = None

  @abc.abstractmethod
  def derive(self, path: pathlib.Path) -> symfs_pb2.Metadata:
    """Derives a Metadata proto given the path.

    Child class must override this method.

    Args:
      path: The path for which to derive metadata.

    Returns: The derived Metadata proto.
    """

  def _pack(self, m: message.Message) -> symfs_pb2.Metadata:
    """Packs the given message into a Metadata proto."""
    metadata = symfs_pb2.Metadata()
    metadata.data.Pack(m)
    return metadata

  def __init__(self, parameters: Optional[any_pb2.Any] = None):
    """Initializes the object with parameters if provided."""
    # Always set parameters if ParametersType is set, regardless of whether
    # parameters argument is given during initialization.
    if self.ParametersType:
      self.parameters = self.ParametersType()

    if parameters and parameters.value:
      if self.ParametersType is None:
        raise ValueError('ParametersType is not set, but parameters provided.')
      parameters.Unpack(self.parameters)
