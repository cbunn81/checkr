import hashlib
from timeit import default_timer as timer
from pathlib import Path
import csv


# To do list
# - DONE - Basic: Run checksum on a directory of files
# - DONE - Basic: Store checksums and filenames in a CSV text file
# - TODO - Basic: Run checksums and compare to those stored
# - TODO - Intermediate: Integrate Typer
# - TODO - Intermediate: Make input directory a command argument
# - TODO - Intermediate: Make output file a command argument
# - TODO - Intermediate: Log errors to a file and stdout
# - TODO - Intermediate: Display progress bar
# - TODO - Intermediate: Allow for levels of verbosity in output
# - TODO - Intermediate: Make hash algorithm a command argument
# - TODO - Intermediate: Allow for a config file to set command arguments
# - TODO - Advanced: Switch to SQLAlchemy ORM instead of CSV files
# - TODO - Advanced: Test multithreading/multiprocessing


def md5(filename: str) -> str:
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def blake2b(filename: str) -> str:
    with open(filename, "rb") as f:
        file_hash = hashlib.blake2b()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def create_checksum(filename: str, algorithm: str = "blake2b"):
    if algorithm == "blake2b":
        return blake2b(filename)
    elif algorithm == "md5":
        return md5(filename)


# TODO - optionally run as recursive
def scan_directory(input_path: str, algorithm: str = "blake2b") -> list[dict]:
    dir = Path(input_path)
    results = []
    if not dir.exists():
        print(f"The directory '{dir}' does not exist.")
        return
    elif not dir.is_dir():
        print(f"'{dir}' is not a directory.")
        return
    else:
        filelist = dir.glob("*")
        for file in filelist:
            # print(str(file))
            # print(type(str(file)))
            # print(blake2b(file))
            results.append(
                {
                    "filename": str(file),
                    "algorithm": algorithm,
                    "checksum": blake2b(file),
                }
            )
        return results


def write_csv(csvfilename: str, results: list[dict]):
    with open(csvfilename, "w", newline="") as csvfile:
        fieldnames = list(results[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def get_stored_checksum_from_csv(
    csvfilename: str, checkfilename: str, algorithm: str = "blake2b"
) -> str:
    with open(csvfilename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["filename"] == checkfilename and row["algorithm"] == algorithm:
                return row["checksum"]


def check_file_against_csv(
    csvfilename: str, checkfilename: str, algorithm: str = "blake2b"
) -> bool:
    stored_checksum = get_stored_checksum_from_csv(
        csvfilename=csvfilename, checkfilename=checkfilename, algorithm=algorithm
    )
    if stored_checksum is not None:
        new_checksum = create_checksum(filename=checkfilename, algorithm=algorithm)
        if stored_checksum == new_checksum:
            print("Checksums match! Yay!")
            return True
        else:
            print("Checksums DON'T match. Oh no!")
            return False
    else:
        print(
            f"No checksum exists for file ({checkfilename}) in CSV file ({csvfilename})."
        )


def check_directory(csvfilename: str, path: str, algorithm: str = "blake2b"):
    dir = Path(path)
    num_good = 0
    num_bad = 0
    total = 0
    if not dir.exists():
        print(f"The directory '{dir}' does not exist.")
        return
    elif not dir.is_dir():
        print(f"'{dir}' is not a directory.")
        return
    else:
        filelist = dir.glob("*")
        for file in filelist:
            if check_file_against_csv(
                csvfilename=csvfilename, checkfilename=str(file), algorithm=algorithm
            ):
                print(f"File ({file}) passed the check.")
                num_good += 1
            else:
                print(f"File ({file}) FAILED the check.")
                num_bad += 1
            total += 1
        print(
            f"Check completed. {num_bad} files failed out of {total} total files checked."
        )


def main():
    directory = "/Users/cbunn/projects/checkr/data/"
    results = scan_directory(directory)
    print(results)
    csvfile = "/Users/cbunn/projects/checkr/results.csv"
    write_csv(csvfile, results)
    check_directory(csvfilename=csvfile, path=directory)


if __name__ == "__main__":
    main()
