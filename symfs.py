from typing import Any, Iterable, Iterator, Mapping, Optional, Set, Tuple

import functools
import itertools
import os
import pathlib
import pprint
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

_APPEND = flags.DEFINE_bool(
    'append', False, 'If set, items specified on the commandline will be '
    'appended to repeatable fields in the config instead of replaced.')

_CONFIG_FILE = flags.DEFINE_string('config_file', None,
                                   'Textproto containing SymFs.Config proto.')

_DRY_RUN = flags.DEFINE_bool('dry_run', False,
                             'If set, only log during generate.')

_GROUP_BY = flags.DEFINE_multi_string(
    'group_by', None, 'Specify a GroupBy in the form of <name>:<field>.')

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


def _generate_combined_groups(
    groups: Tuple[Iterable[Any]],
    parent_groups: Optional[Tuple[str]]) -> Iterator[str]:
  groups = map(lambda group: '-'.join(sorted(map(str, group))), groups)
  if parent_groups is None:
    yield from groups
  else:
    # Note that groups is an iterator; so we iterate it first.
    for group in groups:
      for parent_group in parent_groups:
        yield os.path.join(str(parent_group), group)


def generate_groups(message: message.Message, fields: Iterable[str],
                    max_repeated_group: int, **kwargs) -> Iterator[str]:
  """Yields possible group keys given the message and field.

  This function will generate group keys based on the fields provided in
  `fields`. Each field in `fields` may be repeated in `message`; if this is the
  case, the group keys will come from all possible combinations of the field
  values in the repeated field up to `max_repeated_group`.

  If more than one field is provided in `fields`, the same operation will be
  applied in the given order to create a nested group key until all items in
  `fields` are processed. Basic implementation idea is as follows:

  1. Extract field as an iterable.
  2. Get all possible combination of the field, up to `max_repeated_group`.
  3. Repeat steps 1 and 2 for the next field and combine it with all
     combinations we have for the current field.
  4. Repeat step 3 until we go through each field in `fields`.

  Implementation-wise, we memoize step 2.

  Args:
    message: The message that contains the desired field to get the keys.
    fields: The fields to extract the fields to generate the group keys.
    max_repeated_group: The maximum group size; must be at least 1.
    **kwargs: For internal use.

  Yields:
    Iterables of group keys generated from the message and field.
  """
  if 'parent_groups' in kwargs:
    parent_groups = tuple(kwargs['parent_groups'])
  else:
    parent_groups = None

  if 'combinations_cache' in kwargs:
    combinations_cache = kwargs['combinations_cache']
  else:
    combinations_cache = {}

  extracted_fields = tuple(extract_field_as_iterable(message, fields[0]))
  for group_size in range(
      1, 1 + min((max_repeated_group or 1), len(extracted_fields))):
    combinations_key = (extracted_fields, group_size)
    if combinations_key not in combinations_cache:
      combinations_cache[combinations_key] = tuple(
          itertools.combinations(extracted_fields, group_size))
    groups = combinations_cache[combinations_key]

    if len(fields) == 1:
      yield from _generate_combined_groups(groups, parent_groups)
    else:
      yield from generate_groups(
          message,
          fields[1:],
          max_repeated_group,
          parent_groups=_generate_combined_groups(groups, parent_groups),
          combinations_cache=combinations_cache)


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

    if self.config.metadata_file_patterns:
      logging.warning('Config.metadata_file_patterns is deprecated; '
                      'copying to Config.metadata_files.')
      self.config.metadata_files.patterns.extend(
          self.config.metadata_file_patterns)
      del self.config.metadata_file_patterns[:]

    if self.config.WhichOneof('metadata') is None:
      self.config.metadata_files.patterns.append(r'^metadata\.textproto$')

    for path in itertools.chain((self.config.path,), self.config.source_paths):
      if not pathlib.Path(path).is_absolute():
        logging.warning('%s is not an absolute path; may cause broken links!',
                        path)

    self.paths_by_keys_by_group: GroupToKeyToPathMapping = {}

  def _scan_metadata_files(
      self) -> Iterator[Tuple[pathlib.Path, symfs_pb2.Metadata]]:
    """Yields tuples of directory and associated metadata based on the config.

    Scans the `source_paths` given in the `Config.source_paths` for directories
    that contain `Metadata` files. The `Metadata` files are identified by the
    `Config.metadata_files.patterns`. Assumes `Config.metadata` is set to
    `metadata_files`.

    Yields:
      Tuples of directory and associated metadata for that directory.
    """
    for source_path in self.config.source_paths:
      yielded = False
      for item in pathlib.Path(source_path).rglob('*'):
        if item.is_file() and any(
            re.match(pattern, item.name)
            for pattern in self.config.metadata_files.patterns):
          metadata = symfs_pb2.Metadata()
          text_format.Parse(item.read_text(), metadata)
          yielded = True
          yield item.parent, metadata
      if not yielded:
        logging.warning('No metadata files found in %s.', source_path)

  def _derive_items_metadata(
      self) -> Iterator[Tuple[pathlib.Path, symfs_pb2.Metadata]]:
    """Yields tuples of items and derived metadata based on config.

    As documented in `symfs.proto` for `Config.derived_metadata`, a custom
    function must be specified. Depending on `item_mode`, the file/directory
    will be passed to the custom function, along with the custom `parameters`
    proto, if provided.

    The expected return value will be the derived metadata, which this method
    will yield in addition to the item path itself.

    Yields:
      Tuples of items and associated metadata for that item.
    """
    derived_metadata_function = functools.partial(
        ext_lib.get_derived_metadata_function(
            self.config.derived_metadata.function_name),
        parameters=self.config.derived_metadata.parameters)
    ItemMode = symfs_pb2.Config.DerivedMetadata.ItemMode

    for source_path in self.config.source_paths:
      yielded = False
      for item in pathlib.Path(source_path).rglob('*'):
        if ((self.config.derived_metadata.item_mode
             in (ItemMode.ALL, ItemMode.FILES) and item.is_file()) or
            (self.config.derived_metadata.item_mode
             in (ItemMode.ALL, ItemMode.DIRECTORIES) and item.is_dir())):
          yielded = True
          yield item, derived_metadata_function(item)
      if not yielded:
        logging.warning('No items found in %s.', source_path)

  def scan_metadata(self) -> Iterator[Tuple[pathlib.Path, symfs_pb2.Metadata]]:
    """Yields tuples of items and associated metadata based on Config.metadata.

    The item can be a directory or a file, depending on how Config.metadata is
    written.

    Yields:
      Tuples of items and associated metadata proto for that item.
    """
    which_metadata = self.config.WhichOneof('metadata')
    if which_metadata == 'metadata_files':
      yield from self._scan_metadata_files()
    elif which_metadata == 'derived_metadata':
      yield from self._derive_items_metadata()
    else:
      raise ValueError('None of Config.metadata is set.')

  def _compute_mapping(self) -> None:
    """Computes the mappings from group to group keys to paths."""
    self.paths_by_keys_by_group = {}

    for path, metadata in self.scan_metadata():
      for group_by in self.config.group_by:
        if group_by.name not in self.paths_by_keys_by_group:
          self.paths_by_keys_by_group[group_by.name] = {}

        message = ext_lib.get_prototype(metadata.data.TypeName())()
        metadata.data.Unpack(message)

        # Manually iterate generator to allow for better exception handling.
        group_keys = generate_groups(message, group_by.field,
                                     group_by.max_repeated_group)
        while True:
          try:
            group_key = next(group_keys)
          except StopIteration:
            break
          except AttributeError as error:
            logging.warning(
                '%s: no such field in message type %s; skipping %s.', error,
                metadata.data.TypeName(), path)
            continue
          except TypeError as error:
            logging.warning(
                '%s: the sub-field in %s is not scalar; skipping %s.', error,
                metadata.data.TypeName(), path)
            continue

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
          # We need parents because group_key may be nested.
          (output_path / group_name / group_key).mkdir(
              exist_ok=True, parents=True)
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

  if not _CONFIG_FILE.value and not all(
      (_PATH.value, _SOURCE_PATHS.value, _GROUP_BY.value)):
    raise ValueError('Must provide a config file or flags to build config.')

  config = symfs_pb2.Config()

  if _CONFIG_FILE.value:
    with open(_CONFIG_FILE.value) as stream:
      text_format.Parse(stream.read(), config)

  if _GROUP_BY.value:
    if not _APPEND.value:
      del config.group_by[:]
    for group_by in _GROUP_BY.value:
      name, field = group_by.split(':')
      config.group_by.append(symfs_pb2.Config.GroupBy(name=name, field=[field]))

  if _PATH.value:
    config.path = _PATH.value

  if _SOURCE_PATHS.value:
    if not _APPEND.value:
      del config.source_paths[:]
    config.source_paths.extend(_SOURCE_PATHS.value)

  symfs = SymFs(config)
  logging.debug('\n%s', pprint.pformat(symfs.get_mapping()))
  symfs.generate(dry_run=_DRY_RUN.value)


if __name__ == '__main__':
  app.run(main)
