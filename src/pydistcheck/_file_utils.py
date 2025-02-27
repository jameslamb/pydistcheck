import os
import pathlib
import tarfile
import zipfile
from dataclasses import dataclass
from typing import List, Tuple, Union

from ._compat import _import_zstandard


@dataclass
class _DirectoryInfo:
    name: str


class _ArchiveFormat:
    BZIP2_TAR = ".tar.bz2"
    CONDA = ".conda"
    GZIP_TAR = ".tar.gz"
    ZIP = ".zip"


def _guess_archive_format(filename: str) -> str:
    if filename.lower().endswith("gz"):
        return _ArchiveFormat.GZIP_TAR
    if filename.lower().endswith("bz2"):
        return _ArchiveFormat.BZIP2_TAR
    if filename.lower().endswith(".conda"):
        return _ArchiveFormat.CONDA
    if filename.lower().endswith(".zip"):
        return _ArchiveFormat.ZIP
    if filename.lower().endswith(".whl"):
        return _ArchiveFormat.ZIP

    raise ValueError(
        f"File '{filename}' does not appear to be a Python package distribution in "
        "one of the formats supported by 'pydistcheck'. "
        "Supported formats: .conda, .tar.bz2, .tar.gz, .whl, .zip"
    )


@dataclass
class _FileInfo:
    name: str
    file_format: str
    file_extension: str
    is_compiled: bool
    uncompressed_size_bytes: int

    @classmethod
    def from_tarfile_member(
        cls, *, archive_file: tarfile.TarFile, tar_info: tarfile.TarInfo
    ) -> "_FileInfo":
        member_name = tar_info.name
        file_format, is_compiled = _guess_archive_member_file_format(
            archive_file=archive_file, member_name=member_name
        )
        return cls(
            name=member_name,
            file_format=file_format,
            file_extension=pathlib.Path(member_name).suffix or "no-extension",
            is_compiled=is_compiled,
            uncompressed_size_bytes=tar_info.size,
        )

    @classmethod
    def from_zipfile_member(
        cls, *, archive_file: zipfile.ZipFile, zip_info: zipfile.ZipInfo
    ) -> "_FileInfo":
        member_name = zip_info.filename
        file_format, is_compiled = _guess_archive_member_file_format(
            archive_file=archive_file, member_name=member_name
        )
        return cls(
            name=member_name,
            file_format=file_format,
            file_extension=pathlib.Path(member_name).suffix or "no-extension",
            is_compiled=is_compiled,
            uncompressed_size_bytes=zip_info.file_size,
        )


# references:
#   * https://en.wikipedia.org/wiki/List_of_file_signatures
#   * https://github.com/apple-oss-distributions/xnu/blob/5c2921b07a2480ab43ec66f5b9e41cb872bc554f/EXTERNAL_HEADERS/mach-o/loader.h#L65
#   * https://github.com/apple-oss-distributions/cctools/blob/658da8c66b4e184458f9c810deca9f6428a773a5/include/mach-o/fat.h#L48
#   * https://github.com/matthew-brett/delocate/blob/df86dddd7c94a93b5c03948b8c127ba0777e2a4d/delocate/tools.py#L166
#   * https://learn.microsoft.com/en-us/previous-versions/ms809762(v=msdn.10)
#   * https://en.wikipedia.org/wiki/Portable_Executable

# DOS MZ (.dll, .exe)
_DOS_MZ_MAGIC_FIRST_2_BYTES = {
    0x5A4D.to_bytes(2, "little"),
}

# ELF (.so, .o)
_ELF_MAGIC_FIRST_4_BYTES = {
    0x7F454C46.to_bytes(4, "little"),
    0x7F454C46.to_bytes(4, "big"),
}

# MACH-O (.dylib)
_MACH_O_MAGIC_FIRST_4_BYTES = {
    0xFEEDFACE.to_bytes(4, "little"),  # 32-bit
    0xFEEDFACE.to_bytes(4, "big"),  # 32-bit
    0xFEEDFACF.to_bytes(4, "little"),  # 64-bit
    0xFEEDFACF.to_bytes(4, "big"),  # 64-bit
    0xCAFEBABE.to_bytes(4, "big"),  # mach-o fat binary
    0xCAFEBABF.to_bytes(4, "big"),  # mach-o fat binary
}


class _FileFormat:
    ELF = "ELF"
    MACH_O = "Mach-O"
    OTHER = "Other"
    WINDOWS_PE = "Windows PE"


def _guess_archive_member_file_format(
    *, archive_file: Union[tarfile.TarFile, zipfile.ZipFile], member_name: str
) -> Tuple[str, bool]:
    """
    The approach in this function was inspired by similar code in
    https://github.com/matthew-brett/delocate, so that project's license is included
    in distributions of ``pydistcheck`` as file ``DELOCATE_LICENSE``.

    Returns a two-item tuple of the form ``(file_format, is_compiled)``.
    """
    if isinstance(archive_file, zipfile.ZipFile):
        with archive_file.open(name=member_name, mode="r") as f:
            header = f.read(4)
    else:
        fileobj = archive_file.extractfile(member_name)
        if fileobj is None:  # pragma: no cover
            error_msg = (
                f"'{member_name}' not found. This is a bug in pydistcheck."
                "Report it at https://github.com/jameslamb/pydistcheck/issues."
            )
            raise RuntimeError(error_msg)
        header = fileobj.read(4)

    if header in _ELF_MAGIC_FIRST_4_BYTES:
        return _FileFormat.ELF, True
    if header in _MACH_O_MAGIC_FIRST_4_BYTES:
        return _FileFormat.MACH_O, True
    if header[:2] in _DOS_MZ_MAGIC_FIRST_2_BYTES:
        return _FileFormat.WINDOWS_PE, True

    return _FileFormat.OTHER, False


def _decompress_zstd_archive(*, tar_zst_file: str, decompressed_tar_path: str) -> None:
    """Given a path to a .tar.zst file, decompress its contents to a .tar file"""
    zstandard = _import_zstandard()
    with open(tar_zst_file, "rb") as compressed:
        decompressor = zstandard.ZstdDecompressor()
        with open(decompressed_tar_path, "wb") as destination:
            decompressor.copy_stream(compressed, destination)


def _extract_subset_of_files_from_archive(
    *, archive_file: str, archive_format: str, relative_paths: List[str], out_dir: str
) -> None:
    """
    Extract a subset of files from an archive to a destination directory.

    Extracts AT LEAST those files... might in some cases extract all files.
    """
    if archive_format == _ArchiveFormat.ZIP:
        with zipfile.ZipFile(archive_file, mode="r") as zf:
            zf.extractall(path=out_dir, members=relative_paths)
    elif archive_format == _ArchiveFormat.BZIP2_TAR:
        with tarfile.open(archive_file, mode="r:bz2") as tf:
            tf.extractall(
                path=out_dir,
                members=[tf.getmember(p) for p in relative_paths],
                filter="data",
            )
    elif archive_format == _ArchiveFormat.GZIP_TAR:
        with tarfile.open(archive_file, mode="r:gz") as tf:
            tf.extractall(
                path=out_dir,
                members=[tf.getmember(p) for p in relative_paths],
                filter="data",
            )
    elif archive_format == _ArchiveFormat.CONDA:
        inner_tar_zst_files = []
        # extract any files at the outer ZIP level,
        # and pull out the .tar.zst files
        with zipfile.ZipFile(archive_file, mode="r") as zf:
            for zip_info in zf.infolist():
                # case 1 - skip directories
                if zip_info.is_dir():
                    continue  # pragma: no cover

                # case 2 - if file is in the outer ZIP archive, extract it
                if not zip_info.filename.endswith("tar.zst"):  # pragma: no cover
                    if zip_info.filename in relative_paths:
                        zf.extractall(path=out_dir, members=[zip_info.filename])
                    continue

                # case 3 - one of the zstandard-compressed archives
                inner_tar_zst_files.append(os.path.join(out_dir, zip_info.filename))
                zf.extractall(path=out_dir, members=[zip_info.filename])

        # extract any of these files found in those .tar.zst files
        for tar_zst_file in inner_tar_zst_files:
            # decompress the .tar.zst to just .tar
            decompressed_tar_path = tar_zst_file.replace(".tar.zst", ".tar")
            _decompress_zstd_archive(
                tar_zst_file=tar_zst_file, decompressed_tar_path=decompressed_tar_path
            )

            # do tarfile things
            with tarfile.open(decompressed_tar_path, mode="r") as tf:
                files_to_extract = [
                    tar_info
                    for tar_info in tf.getmembers()
                    if tar_info.name in relative_paths
                ]
                tf.extractall(
                    path=out_dir,
                    members=files_to_extract,
                    filter="data",
                )
