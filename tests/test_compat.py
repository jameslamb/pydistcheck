import sys
from unittest import mock

import pytest

from pydistcheck._compat import _import_zstandard


def test_import_zstandard_raises_informative_error_if_it_isnt_found():
    with mock.patch.dict(sys.modules):
        sys.modules["zstandard"] = None

        with pytest.raises(
            ModuleNotFoundError,
            match="Checking zstd-compressed files requires the 'zstandard' library",
        ):
            _import_zstandard()
