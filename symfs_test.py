from pathlib import Path, PosixPath
from unittest import mock

import os
import pathlib
import re
import tempfile

from absl.testing import absltest
from absl.testing import flagsaver
from absl.testing import parameterized
from google.protobuf import any_pb2
from google.protobuf import text_format
from rules_python.python.runfiles import runfiles

import ext_lib
import ext_pb2
import symfs
import symfs_pb2

r = runfiles.Create()
TEST_CONFIG_FILE = r.Rlocation('everchanging/test_data/config.textproto')
TEST_DATA_DIR = r.Rlocation('everchanging/test_data')
TEST_FROM_STATEMENTS_FILE = r.Rlocation(
    'everchanging/test_data/from_statements.textproto')
TEST_MESSAGE_FILE = r.Rlocation('everchanging/test_data/test_message.textproto')
TEST_METADATA_FILE = r.Rlocation('everchanging/test_data/metadata.textproto')
TEST_STATEMENTS_DIR = r.Rlocation('everchanging/test_data/statements')

# Expected mapping for TEST_CONFIG_FILE under test_data directory.
EXPECTED_MAPPING: symfs.GroupToKeyToPathMapping = {
    'by_s': {
        's_value': {PosixPath(TEST_DATA_DIR)},
    },
    'by_rs': {
        'rs_value_0': {PosixPath(TEST_DATA_DIR)},
        'rs_value_1': {PosixPath(TEST_DATA_DIR)},
        'rs_value_0-rs_value_1': {PosixPath(TEST_DATA_DIR)}
    },
    'by_m': {
        'v_value': {PosixPath(TEST_DATA_DIR)},
    },
}

map_statements = lambda s: set(
    map(lambda f: PosixPath(os.path.join(TEST_STATEMENTS_DIR, f)), s))
# Expected mapping for TEST_FROM_STATEMENTS_FILE under TEST_STATEMENTS_DIR.
EXPECTED_FROM_STATEMENTS_MAPPING: symfs.GroupToKeyToPathMapping = {
    'by_institution': {
        'Chase/credit-card/2018':
            map_statements({'Chase/credit-card/20180102-statements-x1234-.pdf'}
                          ),
        'Chase/credit-card-2/2020':
            map_statements(
                {'Chase/credit-card-2/20200602-statements-4321-.pdf'}),
        'Chase/credit-card-2/2021':
            map_statements(
                {'Chase/credit-card-2/20211202-statements-4321-.pdf'}),
        'Discover/it-card/2021':
            map_statements({
                'Discover/it-card/Discover-Statement-20211003-1234.pdf',
                'Discover/it-card/Discover-Statement-20211103-1234.pdf',
                'Discover/it-card/Discover-Statement-20211203-1234.pdf'
            }),
    },
    'by_date': {
        '2018/01':
            map_statements({'Chase/credit-card/20180102-statements-x1234-.pdf'}
                          ),
        '2020/06':
            map_statements(
                {'Chase/credit-card-2/20200602-statements-4321-.pdf'}),
        '2021/10':
            map_statements(
                {'Discover/it-card/Discover-Statement-20211003-1234.pdf'}),
        '2021/11':
            map_statements(
                {'Discover/it-card/Discover-Statement-20211103-1234.pdf'}),
        '2021/12':
            map_statements({
                'Discover/it-card/Discover-Statement-20211203-1234.pdf',
                'Chase/credit-card-2/20211202-statements-4321-.pdf',
            }),
    },
}


def mock_derived_metadata_derivation(
    path: Path, parameters: any_pb2.Any) -> symfs_pb2.Metadata:
  """Mock custom derived metadata function.

  The metadata this function generates will be simply a copy of the parameters,
  which is assumed to be everchanging.symfs.ext.TestMessage, with TestMessage.s
  replaced with the path as a string.

  Args:
    path: The file path to derive metadata.
    parameters: Assumed to be everchanging.symfs.ext.TestMessage

  Returns:
    Metadata proto with TestMessage and TestMessage.s replaced with the path.
  """
  test_message = ext_pb2.TestMessage()
  parameters.Unpack(test_message)

  test_message.s = str(path)

  metadata = symfs_pb2.Metadata()
  metadata.data.Pack(test_message)

  return metadata


class SymFsTest(parameterized.TestCase):
  """Tests for SymFs functionality."""

  @parameterized.named_parameters(
      ('nested_single', 'm.value', ['v_value']),
      ('repeated', 'rs', ['rs_value_0', 'rs_value_1']),
      ('single', 's', ['s_value']),
  )
  def test_extract_field_as_iterable(self, field, expected_output):
    """Ensures different field structures are properly extracted."""
    message = ext_pb2.TestMessage()

    with open(TEST_MESSAGE_FILE) as stream:
      text_format.Parse(stream.read(), message)

    self.assertEqual(
        symfs.extract_field_as_iterable(message, field), expected_output)

  @parameterized.named_parameters(
      ('multi_group_key', ['rs'], 2, {
          'rs_value_0',
          'rs_value_1',
          'rs_value_0-rs_value_1',
      }),
      ('single_group_key', ['rs'], 1, {
          'rs_value_0',
          'rs_value_1',
      }),
      ('nested_single_group_key', ['rs', 'm.value'], 1, {
          'rs_value_0/v_value',
          'rs_value_1/v_value',
      }),
      ('nested_two_group_key', ['rs', 'm.value'], 2, {
          'rs_value_0/v_value',
          'rs_value_1/v_value',
          'rs_value_0-rs_value_1/v_value',
      }),
      ('nested_multi_group_key', ['rs', 'm.rv'], 2, {
          'rs_value_0/rv_0',
          'rs_value_0/rv_1',
          'rs_value_0/rv_2',
          'rs_value_0/rv_3',
          'rs_value_0/rv_0-rv_1',
          'rs_value_0/rv_0-rv_2',
          'rs_value_0/rv_0-rv_3',
          'rs_value_0/rv_1-rv_2',
          'rs_value_0/rv_1-rv_3',
          'rs_value_0/rv_2-rv_3',
          'rs_value_1/rv_0',
          'rs_value_1/rv_1',
          'rs_value_1/rv_2',
          'rs_value_1/rv_3',
          'rs_value_1/rv_0-rv_1',
          'rs_value_1/rv_0-rv_2',
          'rs_value_1/rv_0-rv_3',
          'rs_value_1/rv_1-rv_2',
          'rs_value_1/rv_1-rv_3',
          'rs_value_1/rv_2-rv_3',
          'rs_value_0-rs_value_1/rv_0',
          'rs_value_0-rs_value_1/rv_1',
          'rs_value_0-rs_value_1/rv_2',
          'rs_value_0-rs_value_1/rv_3',
          'rs_value_0-rs_value_1/rv_0-rv_1',
          'rs_value_0-rs_value_1/rv_0-rv_2',
          'rs_value_0-rs_value_1/rv_0-rv_3',
          'rs_value_0-rs_value_1/rv_1-rv_2',
          'rs_value_0-rs_value_1/rv_1-rv_3',
          'rs_value_0-rs_value_1/rv_2-rv_3',
      }),
      ('nested_multi_group_key_flip', ['m.rv', 'rs'], 2, {
          'rv_0/rs_value_0',
          'rv_1/rs_value_0',
          'rv_2/rs_value_0',
          'rv_3/rs_value_0',
          'rv_0-rv_1/rs_value_0',
          'rv_0-rv_2/rs_value_0',
          'rv_0-rv_3/rs_value_0',
          'rv_1-rv_2/rs_value_0',
          'rv_1-rv_3/rs_value_0',
          'rv_2-rv_3/rs_value_0',
          'rv_0/rs_value_1',
          'rv_1/rs_value_1',
          'rv_2/rs_value_1',
          'rv_3/rs_value_1',
          'rv_0-rv_1/rs_value_1',
          'rv_0-rv_2/rs_value_1',
          'rv_0-rv_3/rs_value_1',
          'rv_1-rv_2/rs_value_1',
          'rv_1-rv_3/rs_value_1',
          'rv_2-rv_3/rs_value_1',
          'rv_0/rs_value_0-rs_value_1',
          'rv_1/rs_value_0-rs_value_1',
          'rv_2/rs_value_0-rs_value_1',
          'rv_3/rs_value_0-rs_value_1',
          'rv_0-rv_1/rs_value_0-rs_value_1',
          'rv_0-rv_2/rs_value_0-rs_value_1',
          'rv_0-rv_3/rs_value_0-rs_value_1',
          'rv_1-rv_2/rs_value_0-rs_value_1',
          'rv_1-rv_3/rs_value_0-rs_value_1',
          'rv_2-rv_3/rs_value_0-rs_value_1',
      }),
  )
  def test_generate_groups(self, fields, max_repeated_group, expected_output):
    """Ensures expected groups are generated."""
    message = ext_pb2.TestMessage()

    with open(TEST_MESSAGE_FILE) as stream:
      text_format.Parse(stream.read(), message)

    self.assertEqual(
        set(symfs.generate_groups(message, fields, max_repeated_group)),
        expected_output)

  def test_symfs_checks_path(self):
    """Ensures SymFs checks if path is set."""
    config = symfs_pb2.Config()
    with self.assertRaisesRegex(ValueError, 'The path field must be set.'):
      symfs.SymFs(config)

  @parameterized.named_parameters(
      ('metadata_files', TEST_CONFIG_FILE, [('by_m', ['m.value'])
                                           ], TEST_DATA_DIR, EXPECTED_MAPPING),
      ('derived_metadata', TEST_FROM_STATEMENTS_FILE, [], TEST_STATEMENTS_DIR,
       EXPECTED_FROM_STATEMENTS_MAPPING),
  )
  def test_compute_mapping(self, config_file, additional_group_bys, source_path,
                           expected_mapping):
    """Ensures mapping can be correctly computed; also tests scan_metadata."""
    config = symfs_pb2.Config()
    with open(config_file) as stream:
      text_format.Parse(stream.read(), config)

    config.source_paths.append(source_path)
    for group_by in additional_group_bys:
      config.group_by.add(
          name=group_by[0],
          field=group_by[1],
      )

    self.assertEqual(symfs.SymFs(config).get_mapping(), expected_mapping)

  def test_generate_from_main(self):
    """E2E test to ensure SymFs is correctly generated."""
    not_exist = '{}: no such field in message type {}; skipping'
    not_scalar = '{}: the sub-field in {} is not scalar; skipping'
    expected_warnings = [
        not_exist.format('s', 'everchanging.symfs.ext.Media'),
        not_exist.format('rs', 'everchanging.symfs.ext.Media'),
        not_exist.format('m', 'everchanging.symfs.ext.Media'),
        # For m.value.
        not_exist.format('m', 'everchanging.symfs.ext.Media'),
        not_scalar.format('InnerTestMessage',
                          'everchanging.symfs.ext.TestMessage'),
        'No metadata files found in /does/not/exist.',
    ]

    with tempfile.TemporaryDirectory() as output_path:
      with flagsaver.flagsaver(
          (symfs._APPEND, True), (symfs._CONFIG_FILE, TEST_CONFIG_FILE),
          (symfs._GROUP_BY, ['by_m:m.value', 'by_m:m']),
          (symfs._PATH, output_path),
          (symfs._SOURCE_PATHS, [TEST_DATA_DIR, '/does/not/exist'])):
        with self.assertLogs(level='WARNING') as logs:
          symfs.main(None)
          self.assertLen(logs.output, len(expected_warnings))
          # Not checking actual log content because the format may be different
          # depending on the underlying Python version, which we don't control.

      mapping = {}
      for group_path in Path(output_path).glob('*'):
        mapping[group_path.name] = {}
        for group_key_path in group_path.glob('*'):
          mapping[group_path.name][group_key_path.name] = set(
              map(Path.resolve, group_key_path.glob('*')))

      self.assertDictEqual(mapping, EXPECTED_MAPPING)

  def test_dry_run(self):
    """Ensures dry_run does not create anything."""
    with tempfile.TemporaryDirectory() as output_path:
      with flagsaver.flagsaver(
          (symfs._CONFIG_FILE, TEST_CONFIG_FILE),
          (symfs._SOURCE_PATHS, [TEST_DATA_DIR, '/does/not/exist']),
          (symfs._PATH, output_path), (symfs._DRY_RUN, True)):
        symfs.main(None)

      self.assertEmpty(set(Path(output_path).rglob('*')))

  @parameterized.parameters(
      ('/absolute/path', './relative/path'),
      ('./relative/path', '/absolute/path'),
  )
  def test_relative_path_warning(self, path, source_path):
    """Ensures warning is sent for relative paths."""
    config = symfs_pb2.Config(path=path, source_paths=(source_path,))
    with self.assertLogs(level='WARNING') as logs:
      symfs.SymFs(config)
      self.assertLen(logs.output, 1)
      self.assertIn(
          './relative/path is not an absolute path; may cause broken links!',
          logs.output[0])

  def test_derived_metadata(self):
    """Ensures correct generation of derived metadata.

    This test is mainly concerned with ensuring that derived metadata are
    generated in the proper manner. As such, the test will simply ensure the
    appropriate functions are called.
    """
    test_message = ext_pb2.TestMessage()
    with open(TEST_MESSAGE_FILE) as stream:
      text_format.Parse(stream.read(), test_message)
    test_parameters = any_pb2.Any()
    test_parameters.Pack(test_message)

    config = symfs_pb2.Config()
    with open(TEST_CONFIG_FILE) as stream:
      text_format.Parse(stream.read(), config)
    config.source_paths.append(TEST_DATA_DIR)

    # This will automatically overwrite the oneof.
    config.derived_metadata.item_mode = symfs_pb2.Config.DerivedMetadata.ItemMode.FILES
    config.derived_metadata.derivation_name = 'the.function.name'
    config.derived_metadata.parameters.CopyFrom(test_parameters)

    with mock.patch.object(
        ext_lib, 'get_derived_metadata_derivation',
        autospec=True) as mock_get_derived_metadata_derivation:
      mock_get_derived_metadata_derivation.return_value = mock_derived_metadata_derivation

      # We will just check the first metadata, as the mock custom function does
      # not do anything special other than add the path to Metadata.data.
      path, metadata = next(symfs.SymFs(config).scan_metadata())

    expected_metadata = symfs_pb2.Metadata()
    test_message.s = str(path)
    expected_metadata.data.Pack(test_message)

    self.assertEqual(metadata, expected_metadata)

  def test_derived_metadata_unmatched(self):
    """Ensures items only match those specified."""
    config = symfs_pb2.Config()
    with open(TEST_CONFIG_FILE) as stream:
      text_format.Parse(stream.read(), config)

    # This will automatically overwrite the oneof.
    config.derived_metadata.item_mode = symfs_pb2.Config.DerivedMetadata.ItemMode.FILES
    config.derived_metadata.derivation_name = 'the.function.name'

    with mock.patch.object(
        ext_lib, 'get_derived_metadata_derivation',
        autospec=True) as mock_get_derived_metadata_derivation:
      mock_get_derived_metadata_derivation.return_value = mock_derived_metadata_derivation

      with tempfile.TemporaryDirectory() as no_files_path:
        pathlib.Path(f'{no_files_path}/test').mkdir()
        config.source_paths.append(no_files_path)
        with self.assertLogs(level='WARNING') as logs:
          list(symfs.SymFs(config).scan_metadata())

          self.assertLen(logs.output, 1)
          self.assertIn(f'No items found in {config.source_paths[0]}',
                        logs.output[0])


if __name__ == '__main__':
  absltest.main()
