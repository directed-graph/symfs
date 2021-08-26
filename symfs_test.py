from pathlib import PosixPath

import unittest

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
    expected_output = {
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

    config = symfs_pb2.Config()
    with open(TEST_CONFIG_FILE) as stream:
      text_format.Parse(stream.read(), config)
    config.source_paths[0] = config.source_paths[0].replace(
        '{TEST_DATA_DIR}', TEST_DATA_DIR)

    self.assertEqual(symfs.SymFs(config).get_mapping(), expected_output)


if __name__ == '__main__':
  unittest.main()