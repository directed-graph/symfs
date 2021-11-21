"""Functions to derive metadata for everchanging.symfs.ext.GenericValues."""

from typing import Iterator

import pathlib
import random

from derived_metadata.abstract_derived_metadata import AbstractDerivedMetadata
from google.protobuf import any_pb2

import symfs_pb2
import ext_pb2


class FixedGrouping(AbstractDerivedMetadata):
  """Derive fixed grouping metadata.

  The general idea is to create a fixed size set of groups (identified by
  numbers, which will be defined by the GenericValues.number field). Each item
  will be given one or more number, and SymFs will then group those items into
  the respective groups per the `number` field.

  Implementation-wise, we will create a list of numbers that represent the
  group, and simply iterate it as we assign the groups. We use a list instead
  of a simple counter to support randomness; that is, with randomness, we can
  simply just shuffle that list on each pass.

  We choose to keep track of all groups in a list to enforce the fact that the
  size of each group will only differ by a maximal of 1.

  Attributes:
    current: An iterator to the next group.
  """

  ParametersType = ext_pb2.GenericValues.FixedGroupingParameters

  def _generate_current_iter(self) -> Iterator[int]:
    """Generates the `current` iterator."""
    num_groups = self.parameters.num_groups
    if num_groups < 1:
      num_groups = 10

    groups = list(range(num_groups))

    while True:
      if self.parameters.random:
        random.shuffle(groups)
      yield from iter(groups)

  def __init__(self, *args, **kwargs):
    """Initializes the `current` iterator."""
    super().__init__(*args, **kwargs)
    self.current = self._generate_current_iter()

    # Store as class attribute so we can just perform logic once.
    self._per_group = self.parameters.per_group
    if self._per_group < 1:
      self._per_group = 1

  def derive(self, path: pathlib.Path) -> symfs_pb2.Metadata:
    """Derives a GenericValues proto that groups items into fixed chunks."""
    # The path itself does not influence the output.
    del path

    generic_values = ext_pb2.GenericValues()
    for _ in range(self._per_group):
      generic_values.numbers.append(next(self.current))

    return self._pack(generic_values)
