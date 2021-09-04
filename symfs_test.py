from pathlib import Path, PosixPath

import tempfile

from absl.testing import absltest
from absl.testing import flagsaver
from absl.testing import parameterized
from google.protobuf import text_format
from rules_python.python.runfiles import runfiles

import ext_pb2
import symfs
import symfs_pb2

r = runfiles.Create()
TEST_CONFIG_FILE = r.Rlocation('everchanging/test_data/config.textproto')
TEST_MESSAGE_FILE = r.Rlocation('everchanging/test_data/test_message.textproto')
TEST_METADATA_FILE = r.Rlocation('everchanging/test_data/metadata.textproto')
TEST_DATA_DIR = r.Rlocation('everchanging/test_data')

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
      ('multi_group_key', 2, {
          ('rs_value_0',),
          ('rs_value_1',),
          ('rs_value_0', 'rs_value_1'),
      }),
      ('single_group_key', 1, {
          ('rs_value_0',),
          ('rs_value_1',),
      }),
  )
  def test_generate_groups(self, max_repeated_group, expected_output):
    """Ensures expected groups are generated."""
    message = ext_pb2.TestMessage()

    with open(TEST_MESSAGE_FILE) as stream:
      text_format.Parse(stream.read(), message)

    self.assertEqual(
        set(symfs.generate_groups(message, 'rs', max_repeated_group)),
        expected_output)

  def test_compute_mapping(self):
    """Ensures mapping can be correctly computed; also tests scan_metadata."""
    config = symfs_pb2.Config()
    with open(TEST_CONFIG_FILE) as stream:
      text_format.Parse(stream.read(), config)
    config.source_paths[0] = config.source_paths[0].replace(
        '{TEST_DATA_DIR}', TEST_DATA_DIR)

    self.assertEqual(symfs.SymFs(config).get_mapping(), EXPECTED_MAPPING)

  def test_generate_from_main(self):
    """E2E test to ensure SymFs is correctly generated."""
    unable_to_extract = 'Unable to extract field {} from message type {}'
    expected_warnings = [
        unable_to_extract.format('s', 'everchanging.symfs.ext.Media'),
        unable_to_extract.format('rs', 'everchanging.symfs.ext.Media'),
        unable_to_extract.format('m.value', 'everchanging.symfs.ext.Media'),
        'No metadata files found in /does/not/exist.',
    ]

    with tempfile.TemporaryDirectory() as output_path:
      with flagsaver.flagsaver(
          (symfs._CONFIG_FILE, TEST_CONFIG_FILE),
          (symfs._SOURCE_PATHS, [TEST_DATA_DIR, '/does/not/exist']),
          (symfs._PATH, output_path)):
        with self.assertLogs(level='WARNING') as logs:
          symfs.main(None)
          self.assertLen(logs.output, len(expected_warnings))
          for actual, regex in zip(logs.output, expected_warnings):
            self.assertRegex(actual, regex)

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


if __name__ == '__main__':
  absltest.main()
