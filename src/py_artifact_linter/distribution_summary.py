import pathlib
import tarfile
from collections import defaultdict


def summarize_distribution_contents(file: str):
    print(f"checking file '{file}'")

    size_by_file_extension = defaultdict(int)

    with tarfile.open(file, mode="r:gz") as tf:
        all_members = tf.getmembers()

        num_files = 0
        num_directories = 0
        num_other_members = 0
        # top_level_dir: str = ""
        for i, member in enumerate(all_members):
            # if i == 0:
            #     top_level_dir = member.name
            if member.isfile():
                num_files += 1
                file_name = member.name
                file_extension = pathlib.Path(file_name).suffix
                compressed_size_in_bytes = member.size
                if file_extension == "":
                    file_extension = "no-extension"
                size_by_file_extension[file_extension] += compressed_size_in_bytes
            elif member.isdir():
                num_directories += 1
            else:
                num_other_members += 1

    print("contents")
    print(f"  * directories: {num_directories}")
    print(f"  * files: {num_files}")
    print(f"  * other: {num_other_members}")
    print("sizes")
    for extension, size in size_by_file_extension.items():
        print(f"  * {extension} - {round(size / 1024.0, 1)}K")
