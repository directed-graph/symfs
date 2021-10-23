import pathlib

from absl.testing import absltest
from absl.testing import parameterized
from google.protobuf import any_pb2

import derived_metadata
import ext_pb2

BUILT_IN_TEST_PARAMETERS = [
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
    (pathlib.Path(
        '/to/ETrade/brokerage/Brokerage Statement - XXXX1234 - 202006.pdf'),
     ext_pb2.FinancialStatement(
         institution='ETrade',
         account='brokerage',
         date=ext_pb2.FinancialStatement.Date(
             year='2020',
             month='06',
             day='01',
         ),
     )),
    (pathlib.Path('/Fidelity/Individual/Statement07312021.pdf'),
     ext_pb2.FinancialStatement(
         institution='Fidelity',
         account='Individual',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='07',
             day='31',
         ),
     )),
    (pathlib.Path(
        '/path/to/Marcus/OnlineSavings/STMTCMB100_20190301_1234_LName_123456_654321.pdf'
    ),
     ext_pb2.FinancialStatement(
         institution='Marcus',
         account='OnlineSavings',
         date=ext_pb2.FinancialStatement.Date(
             year='2019',
             month='03',
             day='01',
         ),
     )),
    (pathlib.Path('/path/to/Schwab/IRA/BrokerageStatement0331181234.pdf'),
     ext_pb2.FinancialStatement(
         institution='Schwab',
         account='IRA',
         date=ext_pb2.FinancialStatement.Date(
             year='2018',
             month='03',
             day='31',
         ),
     )),
    (pathlib.Path(
        '/path/to/Schwab/investor-checking/BankStatement0131204321.pdf'),
     ext_pb2.FinancialStatement(
         institution='Schwab',
         account='investor-checking',
         date=ext_pb2.FinancialStatement.Date(
             year='2020',
             month='01',
             day='31',
         ),
     )),
    (pathlib.Path('/path/to/Schwab/portfolio/AccountStatement033121.pdf'),
     ext_pb2.FinancialStatement(
         institution='Schwab',
         account='portfolio',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='03',
             day='31',
         ),
     )),
    (pathlib.Path(
        '/path/Wealthfront/robo/STATEMENT_2020-05_abcd1234_2020-06-01T10_41_04.123-45_67.pdf'
    ),
     ext_pb2.FinancialStatement(
         institution='Wealthfront',
         account='robo',
         date=ext_pb2.FinancialStatement.Date(
             year='2020',
             month='05',
             day='01',
         ),
     )),
    (pathlib.Path(
        '/path/Wealthfront/checking/GREEN_DOT_STATEMENT_2020-08_1234abcd_2020-08-09T08_00_14.654-32_10.pdf'
    ),
     ext_pb2.FinancialStatement(
         institution='Wealthfront',
         account='checking',
         date=ext_pb2.FinancialStatement.Date(
             year='2020',
             month='08',
             day='01',
         ),
     )),
    (pathlib.Path('/path/WellsFargo/account/101421 WellsFargo.pdf'),
     ext_pb2.FinancialStatement(
         institution='WellsFargo',
         account='account',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='10',
             day='14',
         ),
     )),
    (pathlib.Path('/path/Paypal/pay/statement-Apr-2020.pdf'),
     ext_pb2.FinancialStatement(
         institution='Paypal',
         account='pay',
         date=ext_pb2.FinancialStatement.Date(
             year='2020',
             month='04',
             day='01',
         ),
     )),
]

ADDITIONAL_FORMATS_TEST_PARAMETERS = [
    (pathlib.Path('/path/to/something/account-id/abcd-2021-xyz-02-xyz02.pdf'),
     ('abcd-%Y-xyz-%m-xyz%d.pdf',),
     ext_pb2.FinancialStatement(
         institution='something',
         account='account-id',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='02',
             day='02',
         ),
     )),
    (pathlib.Path('/path/to/something/account-id/abcd-2021-xyz-02-xyz02.pdf'), (
        '%Y-%m-%d.pdf',
        'abcd-%Y-xyz-%m-xyz%d.pdf',
    ),
     ext_pb2.FinancialStatement(
         institution='something',
         account='account-id',
         date=ext_pb2.FinancialStatement.Date(
             year='2021',
             month='02',
             day='02',
         ),
     )),
    (pathlib.Path('/path/to/something/account-id/2020-09.pdf'),
     ('%Y-%m-%d.pdf', 'abcd-%Y-xyz-%m-xyz%d.pdf', '%Y-%m.pdf'),
     ext_pb2.FinancialStatement(
         institution='something',
         account='account-id',
         date=ext_pb2.FinancialStatement.Date(
             year='2020',
             month='09',
             day='01',
         ),
     )),
    (pathlib.Path(
        '/path/to/Marcus/OnlineSavings/STMTCMB100_20190301_1234_LName_123456_654321.pdf'
    ), ('%Y-%m-%d.pdf', 'abcd-%Y-xyz-%m-xyz%d.pdf', '%Y-%m.pdf'),
     ext_pb2.FinancialStatement(
         institution='Marcus',
         account='OnlineSavings',
         date=ext_pb2.FinancialStatement.Date(
             year='2019',
             month='03',
             day='01',
         ),
     )),
]


class FinancialsTest(parameterized.TestCase):
  """Tests for financials."""

  @parameterized.parameters(*BUILT_IN_TEST_PARAMETERS)
  def test_built_in_from_statement(self, path, expected_statement):
    """Ensures we get the correct FinancialStatement metadata."""
    metadata = derived_metadata.financials.from_statement(path)
    statement = ext_pb2.FinancialStatement()
    metadata.data.Unpack(statement)
    self.assertEqual(statement, expected_statement)

  @parameterized.parameters(*ADDITIONAL_FORMATS_TEST_PARAMETERS)
  def test_additional_formats_from_statement(self, path, additional_formats,
                                             expected_statement):
    """Ensures additional_formats are used to get FinancialStatement."""
    parameters = any_pb2.Any()
    params = ext_pb2.FinancialStatement.Parameters(
        additional_formats=additional_formats)
    parameters.Pack(params)
    metadata = derived_metadata.financials.from_statement(path, parameters)
    statement = ext_pb2.FinancialStatement()
    metadata.data.Unpack(statement)
    self.assertEqual(statement, expected_statement)

  def test_not_found_from_statement(self):
    """Ensures from_statement fails when we cannot parse."""
    with self.assertRaisesRegex(ValueError, 'Unable to parse date from'):
      derived_metadata.financials.from_statement(
          pathlib.Path('/something/something.pdf'))


if __name__ == '__main__':
  absltest.main()
