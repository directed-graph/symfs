from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2

import derived_metadata
import ext_lib
import protos.ext_pb2 as ext_pb2


class ExtLibTest(parameterized.TestCase):
  """Tests for ext_lib."""

  @parameterized.parameters(
      ('everchanging.symfs.ext.TestMessage', ext_pb2.TestMessage),
      ('everchanging.symfs.ext.Media', ext_pb2.Media),
  )
  def test_get_prototype(self, type_name, expected_prototype):
    """Ensures we get the correct prototype."""
    self.assertEqual(ext_lib.get_prototype(type_name), expected_prototype)

  def test_get_prototype_missing(self):
    """Ensures non-existent prototypes raises an error."""
    type_name = 'does.not.exist'
    with self.assertRaisesRegex(KeyError,
                                f'Unable to find message {type_name}'):
      ext_lib.get_prototype(type_name)

  @parameterized.parameters(
      ('derived_metadata.financials.from_statement_path',
       derived_metadata.financials.from_statement_path),
      ('derived_metadata.generic_values.FixedGrouping',
       derived_metadata.generic_values.FixedGrouping),
  )
  def test_get_derived_metadata_derivation(self, name, expected_derivation):
    """Ensures we get the correct function."""
    self.assertEqual(
        ext_lib.get_derived_metadata_derivation(name), expected_derivation)


if __name__ == '__main__':
  absltest.main()
