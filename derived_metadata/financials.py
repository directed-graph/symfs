"""Functions to derive metadata for financial items."""

import pathlib

from google.protobuf import any_pb2

import symfs_pb2


def from_statements(path: pathlib.Path,
                    parameters: any_pb2.Any) -> symfs_pb2.Metadata:
  """Returns Metadata for financial statements."""
  raise NotImplementedError('from_statements not implemented yet.')
