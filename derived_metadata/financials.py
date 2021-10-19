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

from typing import Callable, Mapping

import pathlib
import re
import time

from google.protobuf import any_pb2

import symfs_pb2
import ext_pb2

GetDateCallable = Callable[[pathlib.Path], str]
_GET_DATE_BY_INSTITUTION: Mapping[str, GetDateCallable] = {}


def _get_institution(path: pathlib.Path) -> str:
  """Returns the institution. As per docstring, this is index -3."""
  return str(path).split('/')[-3]


def _get_account(path: pathlib.Path) -> str:
  """Returns the account identifier. As per docstring, this is index -2."""
  return str(path).split('/')[-2]


def _get_date(path: pathlib.Path) -> time.struct_time:
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
    KeyError: In the event that no per-institution function exist.
  """
  institution = _get_institution(path)
  try:
    return _GET_DATE_BY_INSTITUTION[institution](path)
  except KeyError:
    raise KeyError(f'No _get_date defined for {institution}.')


def from_statement(path: pathlib.Path,
                   parameters: any_pb2.Any) -> symfs_pb2.Metadata:
  """Returns Metadata for financial statement."""
  date = _get_date(path)
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


@_register_get_date('Ally')
def _get_date_from_ally(path: pathlib.Path) -> time.struct_time:
  return time.strptime(path.name, '%b %Y Ally Bank Statement.pdf')


@_register_get_date('Chase')
def _get_date_from_chase(path: pathlib.Path) -> time.struct_time:
  return time.strptime(
      re.match(r'(\d+)-statements-x?\d+-\.pdf', path.name).group(1), '%Y%m%d')


@_register_get_date('Discover')
def _get_date_from_discover(path: pathlib.Path) -> time.struct_time:
  return time.strptime(
      re.match(r'Discover-Statement-(\d+)-\d+\.pdf', path.name).group(1),
      '%Y%m%d')


@_register_get_date('ETrade')
def _get_date_from_etrade(path: pathlib.Path) -> time.struct_time:
  return time.strptime(
      re.match(r'Brokerage Statement - XXXX\d{4} - (\d+)\.pdf',
               path.name).group(1), '%Y%m')


@_register_get_date('Fidelity')
def _get_date_from_fidelity(path: pathlib.Path) -> time.struct_time:
  return time.strptime(
      re.match(r'Statement(\d+)\.pdf', path.name).group(1), '%m%d%Y')


@_register_get_date('Marcus')
def _get_date_from_marcus(path: pathlib.Path) -> time.struct_time:
  return time.strptime(path.name.split('_')[1], '%Y%m%d')
