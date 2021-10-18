import pathlib

from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import descriptor_pb2

import derived_metadata
import ext_pb2

TEST_PARAMETERS = [
    (pathlib.Path(
        '/home/path/to/Ally/consolidated/Sep 2021 Ally Bank Statement.pdf'),
     ext_pb2.FinancialStatement(
         institution='Ally',
         account='consolidated',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='09',
             day='01',
         ),
     )),
    (pathlib.Path(
        '/home/path/to/Chase/credit-card/20211002-statements-1234-.pdf'),
     ext_pb2.FinancialStatement(
         institution='Chase',
         account='credit-card',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='10',
             day='02',
         ),
     )),
    (pathlib.Path(
        '/home/path/to/Discover/it-card/Discover-Statement-20211203-1234.pdf'),
     ext_pb2.FinancialStatement(
         institution='Discover',
         account='it-card',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='12',
             day='03',
         ),
     )),
]


class FinancialsTest(parameterized.TestCase):
  """Tests for financials."""

  @parameterized.parameters(*TEST_PARAMETERS)
  def test_from_statement(self, path, expected_statement):
    """Ensures we get the correct FinancialStatement metadata."""
    metadata = derived_metadata.financials.from_statement(path, None)
    statement = ext_pb2.FinancialStatement()
    metadata.data.Unpack(statement)
    self.assertEqual(statement, expected_statement)


if __name__ == '__main__':
  absltest.main()
