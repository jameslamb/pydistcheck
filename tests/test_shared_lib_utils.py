import subprocess
from unittest.mock import Mock, patch

from pydistcheck._shared_lib_utils import (
    _MACHO_STRIP_SYMBOL,
    _get_symbols,
    _run_command,
)


def test_run_command_handles_binary_output():
    """Test that _run_command can handle binary output containing invalid UTF-8 bytes."""
    mock_output = bytes(
        [0x68, 0x65, 0x6C, 0x6C, 0x6F, 0xD7, 0x77, 0x6F, 0x72, 0x6C, 0x64]
    )  # i.e., "hello" + invalid UTF-8 + "world"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(stdout=mock_output)

        # Should not raise UnicodeDecodeError,
        result = _run_command(["some", "command"])
        # latin1 encoding should preserve all bytes.
        assert len(result) == len(mock_output)
        # Check valid parts of the string.
        assert "hello" in result
        assert "world" in result


def test_run_command_handles_command_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["cmd"])
        result = _run_command(["failing", "command"])
        assert result == "__command_failed__"


def test_run_command_handles_missing_command():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = _run_command(["nonexistent"])
        assert result == "__tool_not_available__"


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
