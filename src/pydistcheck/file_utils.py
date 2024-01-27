class _ArchiveFormat:
    BZIP2_TAR = ".tar.bz2"
    CONDA = ".conda"
    GZIP_TAR = ".tar.gz"
    ZIP = ".zip"


def _guess_archive_format(filename: str) -> str:
    if filename.endswith("gz"):
        return _ArchiveFormat.GZIP_TAR
    if filename.endswith("bz2"):
        return _ArchiveFormat.BZIP2_TAR
    if filename.endswith(".conda"):
        return _ArchiveFormat.CONDA

    return _ArchiveFormat.ZIP
