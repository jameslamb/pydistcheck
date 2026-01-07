import re
import sys
import sysconfig
from unittest import mock

import pytest

from pydistcheck._compat import _import_zstandard, _tf_extractall_has_filter


def test_import_zstandard_raises_informative_error_if_it_isnt_found():
    with mock.patch.dict(sys.modules):
        sys.modules["zstandard"] = None

        with pytest.raises(
            ModuleNotFoundError,
            match="Checking zstd-compressed files requires the 'zstandard' library",
        ):
            _import_zstandard()


def test_extractall_has_filter_works():
    python_major, python_minor, *_ = sysconfig.get_python_version()
    # handle versions with letters, like '3.13t'
    python_minor = re.sub(r"[^0-9.]", "", python_minor)
    res = _tf_extractall_has_filter()
    if int(python_major) >= 3 and int(python_minor) >= 12:
        assert res is True
    else:
        assert isinstance(res, bool)
