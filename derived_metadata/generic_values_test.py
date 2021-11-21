from typing import List
from unittest import mock

import functools
import random

from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import any_pb2

import derived_metadata
import ext_pb2


def _replace_with(items: List[int], value: int) -> List[int]:
  """Replaces all values in items with value (in-place)."""
  length = len(items)
  del items[:]
  items.extend(length * [value])
  return items


def _collect_numbers(
    fixed_grouping: derived_metadata.generic_values.FixedGrouping,
    iterations: int) -> List[int]:
  """Collects the numbers from FixedGrouping derivation."""
  numbers = []
  for _ in range(iterations):
    generic_values = ext_pb2.GenericValues()

    metadata = fixed_grouping.derive(mock.ANY)
    metadata.data.Unpack(generic_values)

    numbers.extend(generic_values.numbers)
  return numbers


def _make_fixed_grouping_parameters(**kwargs) -> any_pb2.Any:
  """Creates FixedGroupingParameters as Any proto from the kwargs."""
  fixed_grouping_parameters = ext_pb2.GenericValues.FixedGroupingParameters(
      **kwargs)
  parameters = any_pb2.Any()
  parameters.Pack(fixed_grouping_parameters)
  return parameters


class GenericValuesTest(parameterized.TestCase):
  """Tests for generic_values."""

  @parameterized.parameters(
      (0, 1, [0]),
      (0, 6, [0, 1, 2, 3, 4, 5]),
      (12, 12, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
  )
  def test_fixed_grouping(self, num_groups: int, iterations: int,
                          expected_numbers: List[int]):
    """Ensures regular fixed grouping works."""

    fixed_grouping = derived_metadata.generic_values.FixedGrouping(
        _make_fixed_grouping_parameters(num_groups=num_groups))
    numbers = _collect_numbers(fixed_grouping, iterations)

  def test_fixed_group_per_grouping(self):
    """Ensures per_group groups each item correctly."""
    fixed_grouping = derived_metadata.generic_values.FixedGrouping(
        _make_fixed_grouping_parameters(per_group=10))

    self.assertEqual(_collect_numbers(fixed_grouping, 1), list(range(10)))

  def test_fixed_grouping_random(self):
    """Ensures randomness works.

    Implementation-wise, we will replace random.shuffle with a function that
    simply replaces all elements with ones that we control.
    """
    iterations = 100
    shuffle_value = 1
    num_groups = 10

    fixed_grouping = derived_metadata.generic_values.FixedGrouping(
        _make_fixed_grouping_parameters(num_groups=num_groups, random=True))

    with mock.patch.object(
        random,
        'shuffle',
        side_effect=functools.partial(_replace_with,
                                      value=shuffle_value)) as mock_shuffle:
      numbers = _collect_numbers(fixed_grouping, iterations)

    self.assertEqual(mock_shuffle.call_count, iterations // num_groups)
    self.assertEqual(numbers, iterations * [shuffle_value])


if __name__ == '__main__':
  absltest.main()
