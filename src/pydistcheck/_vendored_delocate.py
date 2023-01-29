"""
Code copied (with minor modifications) from ``delocate``, to avoid
a runtime dependency on that project.

Source: https://github.com/matthew-brett/delocate

That project's license (as of when the code was copied) is available in this
repository at ``LICENSES/DELOCATE_LICENSE``.
"""

# Mach-O magic numbers. See:
# https://github.com/apple-oss-distributions/xnu/blob/5c2921b07a2480ab43ec66f5b9e41cb872bc554f/EXTERNAL_HEADERS/mach-o/loader.h#L65
# https://github.com/apple-oss-distributions/cctools/blob/658da8c66b4e184458f9c810deca9f6428a773a5/include/mach-o/fat.h#L48
# pragma: no cover
_MACHO_MAGIC = {
    0xFEEDFACE.to_bytes(4, "little"),  # MH_MAGIC
    0xFEEDFACE.to_bytes(4, "big"),  # MH_MAGIC
    0xFEEDFACF.to_bytes(4, "little"),  # MH_MAGIC_64
    0xFEEDFACF.to_bytes(4, "big"),  # MH_MAGIC_64
    0xCAFEBABE.to_bytes(4, "big"),  # FAT_MAGIC (always big-endian)
    0xCAFEBABF.to_bytes(4, "big"),  # FAT_MAGIC_64 (always big-endian)
}


def _is_macho_file(filename: str) -> bool:
    """Return True if file at `filename` begins with Mach-O magic number."""
    try:
        with open(filename, "rb") as f:
            header = f.read(4)
            return header in _MACHO_MAGIC
    except PermissionError:  # pragma: no cover
        return False
    except FileNotFoundError:  # pragma: no cover
        return False
