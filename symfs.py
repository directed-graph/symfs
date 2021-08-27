from pprint import pformat
from typing import Any, Iterable, Iterator, Mapping, Set, Tuple

import itertools
import pathlib
import re

from absl import app
from absl import flags
from absl import logging
from google.protobuf import any_pb2
from google.protobuf import message
from google.protobuf import text_format
from google.protobuf.internal.containers import RepeatedScalarFieldContainer

import ext_lib
import symfs_pb2

_CONFIG_FILE = flags.DEFINE_string('config_file', None,
                                   'Textproto containing SymFs.Config proto.')

_DRY_RUN = flags.DEFINE_bool('dry_run', False,
                             'If set, only log during generate.')

_PATH = flags.DEFINE_string('path', None,
                            'If set, overrides the SymFs.Config.path field.')

_SOURCE_PATHS = flags.DEFINE_multi_string(
    'source_paths', None,
    'If set, overrides the SymFs.Config.source_paths field.')

GroupToKeyToPathMapping = Mapping[str, Mapping[str, Set[pathlib.Path]]]


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


class SymFs:
  """Class to generate items based on the given SymFs config.

  The main item generated by this class is the `GroupToKeyToPathMapping` object
  that can be accessed via `get_mapping()`. This mapping maps the group name,
  as defined in `Config.group_by.name`, to group keys, as obtained from
  `Metadata.data` and selected by `Config.group_by.field`, to a set of paths to
  contain in said group key.
  """

  def __init__(self, config: symfs_pb2.Config) -> None:
    """Initializes the SymFs object and set defaults."""
    self.config = config

    if not self.config.metadata_file_patterns:
      self.config.metadata_file_patterns.append(r'^metadata\.textproto')

    self.paths_by_keys_by_group: GroupToKeyToPathMapping = {}

  def scan_metadata(self) -> Iterator[Tuple[pathlib.Path, symfs_pb2.Metadata]]:
    """Yields tuples of directory and associated metadata based on the config.

    Scans the `source_paths` given in the `Config.source_paths` for directories
    that contain `Metadata` files. The `Metadata` files are identified by the
    `Config.metadata_file_patterns`.

    Yields:
      Tuples of directory and associated metadata for that directory.
    """
    for source_path in self.config.source_paths:
      yielded = False
      for item in pathlib.Path(source_path).rglob('*'):
        if item.is_file() and any(
            re.match(pattern, item.name)
            for pattern in self.config.metadata_file_patterns):
          metadata = symfs_pb2.Metadata()
          text_format.Parse(item.read_text(), metadata)
          yielded = True
          yield item.parent, metadata
      if not yielded:
        logging.warning('No metadata files found in %s.', source_path)

  def _compute_mapping(self) -> None:
    """Computes the mappings from group to group keys to paths."""
    self.paths_by_keys_by_group = {}

    for path, metadata in self.scan_metadata():
      for group_by in self.config.group_by:
        if group_by.name not in self.paths_by_keys_by_group:
          self.paths_by_keys_by_group[group_by.name] = {}

        message = ext_lib.get_prototype(metadata.data.TypeName())()
        metadata.data.Unpack(message)
        for group in generate_groups(message, group_by.field,
                                     group_by.max_repeated_group):
          group_key = '-'.join(sorted(group))
          try:
            self.paths_by_keys_by_group[group_by.name][group_key].add(path)
          except KeyError:
            self.paths_by_keys_by_group[group_by.name][group_key] = {path}

  def get_mapping(self) -> GroupToKeyToPathMapping:
    """Returns the mappings from group to group keys to paths."""
    if not self.paths_by_keys_by_group:
      self._compute_mapping()

    return self.paths_by_keys_by_group

  def generate(self, dry_run: bool = False):
    """Generates the SymFs."""
    output_path = pathlib.Path(self.config.path)
    if not output_path.exists():
      if not dry_run:
        output_path.mkdir(parents=True)
      logging.info('Created path %s.', output_path)
    for group_name, group in self.get_mapping().items():
      if not dry_run:
        (output_path / group_name).mkdir(exist_ok=True)
      for group_key, group_items in group.items():
        if not dry_run:
          (output_path / group_name / group_key).mkdir(exist_ok=True)
        for item in group_items:
          item_path = output_path / group_name / group_key / item.name
          if item_path.exists():
            logging.warning('%s -> %s already exists; skipping %s.', item_path,
                            item_path.resolve(), item)
            continue
          if not dry_run:
            item_path.symlink_to(item, target_is_directory=True)
          logging.info('%s -> %s', item_path, item)


def main(argv):
  del argv

  if not _CONFIG_FILE.value:
    raise ValueError('Must provide a config.')

  config = symfs_pb2.Config()
  with open(_CONFIG_FILE.value) as stream:
    text_format.Parse(stream.read(), config)

  if _PATH.value:
    config.path = _PATH.value

  if _SOURCE_PATHS.value:
    del config.source_paths[:]
    config.source_paths.extend(_SOURCE_PATHS.value)

  symfs = SymFs(config)
  logging.debug('\n%s', pformat(symfs.get_mapping()))
  symfs.generate(dry_run=_DRY_RUN.value)


if __name__ == '__main__':
  app.run(main)
