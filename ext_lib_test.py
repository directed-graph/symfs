from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2

import ext_lib
import ext_pb2


class ExtLibTest(parameterized.TestCase):
  """Tests for ext_lib."""

  @parameterized.parameters(
      ('everchanging.symfs.ext.TestMessage', ext_pb2.TestMessage),)
  def test_get_prototype(self, type_name, expected_prototype):
    """Ensures we get the correct prototype."""
    self.assertEqual(ext_lib.get_prototype(type_name), expected_prototype)

  @parameterized.parameters(
      ('everchanging.symfs.ext.TestMessage', ext_pb2.TestMessage),)
  def test_get_prototype_self_managed(self, type_name, expected_prototype):
    """Ensures we get the correct prototype for self_managed case."""
    descriptor = descriptor_pb2.DescriptorProto()
    expected_descriptor = descriptor_pb2.DescriptorProto()

    ext_lib.get_prototype(
        type_name, self_managed=True).DESCRIPTOR.CopyToProto(descriptor)
    expected_prototype.DESCRIPTOR.CopyToProto(expected_descriptor)

    self.assertEqual(descriptor, expected_descriptor)


if __name__ == '__main__':
  absltest.main()
