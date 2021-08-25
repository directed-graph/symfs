from typing import Any, Iterable, Iterator, Mapping, Set, Tuple

import itertools

from google.protobuf import message
from google.protobuf.internal.containers import RepeatedScalarFieldContainer


def extract_field_as_iterable(message: message.Message,
                              field: str) -> Iterable[Any]:
  """Returns a potentially nested field of a message as an iterable.

  Note that nested Any protos are not supported. Further, any field other than
  the terminal field cannot be a repeated field.

  Args:
    message: The proto message to extract the field from.
    field: The field to extract. Can be nested (e.g. "a.b.c").

  Returns:
    If the terminal field is a repeated field, that field will be returned. If
    the terminal field is a scalar, then that field will be wrapped in a list.
  """
  current = message
  for field in field.split('.'):
    current = getattr(current, field)
  if isinstance(current, Iterable) and not any(
      isinstance(current, t) for t in (str, bytes)):
    return current
  return [current]


def generate_groups(message: message.Message, field: str,
                    max_repeated_group: int) -> Iterator[Iterable[Any]]:
  """Yields possible groups given the message and field.

  Args:
    message: The message that contains the desired field to get the keys.
    field: The field to extract the fields to generate the group keys.
    max_repeated_group: The maximum group size; must be at least 1.

  Yields:
    Iterables of group keys generated from the message and field.
  """
  groups = extract_field_as_iterable(message, field)
  for group_size in range(1, 1 + (max_repeated_group or 1)):
    yield from itertools.combinations(groups, group_size)
