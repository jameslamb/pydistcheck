from unittest.mock import Mock, patch

from pydistcheck._shared_lib_utils import _MACHO_STRIP_SYMBOL, _get_symbols


def test_get_symbols_filters_radr_symbol():
    """Test that _get_symbols filters out the Mach-O strip symbol."""
    mock_output = (
        "0000000000000000 T _main\n"
        f"0000000005614542 - 00 0000    OPT {_MACHO_STRIP_SYMBOL}\n"
        "0000000000001000 D _data\n"
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(stdout=mock_output.encode())

        result = _get_symbols(["nm", "-a"], "test.dylib")

        # Should keep real symbols but filter out the strip symbol.
        assert "_main" in result
        assert "_data" in result
        assert _MACHO_STRIP_SYMBOL not in result
        assert len(result.split("\n")) == 2  # Only two real symbols
