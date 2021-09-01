from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2

import ext_lib
import ext_pb2


class ExtLibTest(parameterized.TestCase):
  """Tests for ext_lib."""

  @parameterized.parameters(
      ('everchanging.symfs.ext.TestMessage', ext_pb2.TestMessage),
      ('everchanging.symfs.ext.Media', ext_pb2.Media),
  )
  def test_get_prototype(self, type_name, expected_prototype):
    """Ensures we get the correct prototype."""
    self.assertEqual(ext_lib.get_prototype(type_name), expected_prototype)


if __name__ == '__main__':
  absltest.main()
