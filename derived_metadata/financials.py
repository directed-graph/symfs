"""Functions to derive metadata for financial statements.

The general expected structure of financial statements are as follows:

    /.../<institution>/<account>/<per-institution-statement-name>.pdf

For our purposes, the `<institution>` and `<account>` can be mapped to the
FinancialStatement proto directly. We will then derive the date from the
`<per-institution-statement-name>`.

In order to derive the date, a per-institution `_get_date` function will need
to be defined, and then registered via `_register_get_date` decorator. This
mechanism will only be implemented for `_get_date` for now, but we can apply
this idea to `_get_account`, or even, indeed, `_get_institution` in the future.
"""

from typing import Callable, Iterable, Mapping, Optional

import pathlib
import re
import time

from absl import logging
from google.protobuf import any_pb2

import protos.ext_pb2 as ext_pb2
import protos.symfs_pb2 as symfs_pb2

GetDateCallable = Callable[[pathlib.Path], str]
_GET_DATE_BY_INSTITUTION: Mapping[str, GetDateCallable] = {}


def _get_institution(path: pathlib.Path) -> str:
  """Returns the institution. As per docstring, this is index -3."""
  return str(path).split('/')[-3]


def _get_account(path: pathlib.Path) -> str:
  """Returns the account identifier. As per docstring, this is index -2."""
  return str(path).split('/')[-2]


def _get_date(path: pathlib.Path,
              additional_formats: Iterable[str]) -> time.struct_time:
  """Returns the date.

  The date will depend on the institution; it is expected that there exists a
  function specific to the institution to derive the date from the statement
  (either path or content). This per-institution function is to be defined and
  then registered via the _register_get_date decorator.

  Args:
    path: The path from which to get the date.

  Returns:
    The date derived from the path as a time struct.

  Raises:
    ValueError: In the event that we cannot parse the date.
  """
  institution = _get_institution(path)
  try:
    return _GET_DATE_BY_INSTITUTION[institution](path)
  except KeyError:
    logging.warning(
        'No _get_date defined for %s; trying with additional_formats.',
        institution)
  except (AttributeError, ValueError):
    logging.warning(
        'Failed to parse %s for %s; trying with additional_formats.',
        institution, path.name)

  for additional_format in additional_formats:
    try:
      return time.strptime(path.name, additional_format)
    except ValueError:
      logging.warning('Unable to parse with "%s".', additional_format)

  raise ValueError(f'Unable to parse date from {path.name}.')


def from_statement_path(
    path: pathlib.Path,
    parameters: Optional[any_pb2.Any] = None) -> symfs_pb2.Metadata:
  """Returns Metadata for financial statement."""
  params = ext_pb2.FinancialStatement.Parameters()
  if parameters:
    parameters.Unpack(params)

  date = _get_date(path, params.additional_formats)
  metadata = symfs_pb2.Metadata()
  metadata.data.Pack(
      ext_pb2.FinancialStatement(
          institution=_get_institution(path),
          account=_get_account(path),
          date=ext_pb2.FinancialStatement.Date(
              year=f'{date.tm_year:04}',
              month=f'{date.tm_mon:02}',
              day=f'{date.tm_mday:02}',
          ),
      ))
  return metadata


def _register_get_date(
    institution: str) -> Callable[[GetDateCallable], GetDateCallable]:

  def _register_get_date_by_institution(
      function: GetDateCallable) -> GetDateCallable:
    _GET_DATE_BY_INSTITUTION[institution] = function
    return function

  return _register_get_date_by_institution


def _get_date_with_patterns_helper(
    path: pathlib.Path, regex_patterns: Iterable[str],
    date_formats: Iterable[str]) -> time.struct_time:
  for pattern in regex_patterns:
    for date_format in date_formats:
      try:
        return time.strptime(re.match(pattern, path.name).group(1), date_format)
      except (AttributeError, ValueError) as error:
        logging.warning('Unable to parse %s with %s using format %s: %s.',
                        path.name, pattern, date_format, error)

  raise ValueError(f'Failed to parse {path.name}.')


@_register_get_date('Ally')
def _get_date_from_ally(path: pathlib.Path) -> time.struct_time:
  return time.strptime(path.name, '%b %Y Ally Bank Statement.pdf')


@_register_get_date('Chase')
def _get_date_from_chase(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(path, {r'(\d+)-statements-x?\d+-\.pdf'},
                                        {'%Y%m%d'})


@_register_get_date('Discover')
def _get_date_from_discover(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(path,
                                        {r'Discover-Statement-(\d+)-\d+\.pdf'},
                                        {'%Y%m%d'})


@_register_get_date('ETrade')
def _get_date_from_etrade(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(
      path, {r'Brokerage Statement - XXXX\d{4} - (\d+)\.pdf'}, {'%Y%m'})


@_register_get_date('Fidelity')
def _get_date_from_fidelity(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(path, {r'Statement(\d+)\.pdf'},
                                        {'%m%d%Y'})


@_register_get_date('Marcus')
def _get_date_from_marcus(path: pathlib.Path) -> time.struct_time:
  return time.strptime(path.name.split('_')[1], '%Y%m%d')


@_register_get_date('Schwab')
def _get_date_from_schwab(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(
      path, {
          r'AccountStatement(\d{6})\.pdf',
          r'Bank Statement_(\d{4}-\d{2}-\d{2})_\d+\.pdf',
          r'BankStatement(\d{6})\d+\.pdf',
          r'Brokerage Statement_(\d{4}-\d{2}-\d{2})_\d+\.pdf',
          r'BrokerageStatement(\d{6})\d+\.pdf',
      }, {'%Y-%m-%d', '%m%d%y'})


@_register_get_date('Wealthfront')
def _get_date_from_wealthfront(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(
      path, {
          r'GREEN_DOT_STATEMENT_(\d{4}-\d{2})_.*\.pdf',
          r'STATEMENT_(\d{4}-\d{2})_.*\.pdf',
      }, {'%Y-%m'})


@_register_get_date('WellsFargo')
def _get_date_from_wealthfront(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(path, {r'(\d{6}) WellsFargo\.pdf'},
                                        {'%m%d%y'})


@_register_get_date('Paypal')
def _get_date_from_paypal(path: pathlib.Path) -> time.struct_time:
  return _get_date_with_patterns_helper(path, {r'statement-(.*-\d+)\.pdf'},
                                        {'%b-%Y'})
