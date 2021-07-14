# standard library imports
import hashlib
from timeit import default_timer as timer
from pathlib import Path
import csv
import time

# third party imports
import typer
from rich.progress import track


# To do list
# - DONE - Basic: Run checksum on a directory of files
# - DONE - Basic: Store checksums and filenames in a CSV text file
# - DONE - Basic: Run checksums and compare to those stored
# - DONE - Intermediate: Integrate Typer
# - DONE - Intermediate: Make input directory a command argument
# - DONE - Intermediate: Make output file a command argument
# - TODO - Intermediate: Log errors to a file and stdout
# - TODO - Intermediate: Display progress bar
# - TODO - Intermediate: Allow for levels of verbosity in output
# - DONE - Intermediate: Make hash algorithm a command argument
# - TODO - Intermediate: Allow for a list of input directories
# - TODO - Intermediate: Allow for a config file to set command arguments
# - TODO - Advanced: Switch to SQLAlchemy ORM instead of CSV files
# - TODO - Advanced: Test multithreading/multiprocessing

app = typer.Typer(help="File Integrity Checker")


def md5(filename: str) -> str:
    """Get MD5 digest for a file.

    Args:
        filename (str): The file to get an MD5 digest of.

    Returns:
        str: An MD5 digest.
    """
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def blake2b(filename: str) -> str:
    """Get blake2b digest for a file.

    Args:
        filename (str): The file to get a blake2b digest of.

    Returns:
        str: A blake2b hexdigest.
    """
    with open(filename, "rb") as f:
        file_hash = hashlib.blake2b()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def create_checksum(filename: str, algorithm: str = "blake2b") -> str:
    """Create a checksum digest for a file.

    Args:
        filename (str): The file to get a checksum digest of.
        algorithm (str, optional): The checksum algorithm to use. Defaults to "blake2b".

    Returns:
        str: A checksum digest.
    """
    if algorithm == "blake2b":
        return blake2b(filename)
    elif algorithm == "md5":
        return md5(filename)


def write_csv(csvfilename: str, results: list[dict]):
    """Create a CSV file and write the checksum results to it.

    Args:
        csvfilename (str): The file to create.
        results (list[dict]): A list of results to write to the CSV file. Each result is a dictionary with keys: filename, algorithm, checksum.
    """
    with open(csvfilename, "w", newline="") as csvfile:
        fieldnames = list(results[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def get_stored_checksum_from_csv(
    csvfilename: str, checkfilename: str, algorithm: str = "blake2b"
) -> str:
    """Retrieve a stored checksum digest from a CSV file of previous results.

    Args:
        csvfilename (str): A CSV file containing checksum results.
        checkfilename (str): The file to check against the CSV file results.
        algorithm (str, optional): The checksum algorithm to use. Defaults to "blake2b".

    Returns:
        str: The checksum digest stored in the CSV file, if any.
    """
    with open(csvfilename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["filename"] == checkfilename and row["algorithm"] == algorithm:
                return row["checksum"]


def check_file_against_csv(
    csvfilename: str, checkfilename: str, algorithm: str = "blake2b"
) -> bool:
    """Compare a previously generated checksum from a CSV file with a newly generated one.

    Args:
        csvfilename (str): The CSV file containing the previously generated checksum.
        checkfilename (str): The file to check.
        algorithm (str, optional): The checksum algorithm to use. Defaults to "blake2b".

    Returns:
        bool: True if the checksums match, otherwise False.
    """
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


def get_filelist(path: str, recursive: bool = False) -> list[str]:
    """Get a list of files (but not directories) from a path.

    Args:
        path (str): The path to search for files.
        recursive (bool, optional): Whether to recursively search the path. Defaults to False.

    Returns:
        list[str]: A list of all filenames, given as absolute paths.
    """
    dir = Path(path)
    if not dir.exists():
        print(f"The directory '{dir}' does not exist.")
        return
    elif not dir.is_dir():
        print(f"'{dir}' is not a directory.")
        return
    else:
        results = dir.rglob("*") if recursive else dir.glob("*")
        filelist = [x for x in results if x.is_file()]
        return filelist


@app.command()
def scan(
    path: str = typer.Argument(..., help="The path containing files to be checked."),
    csvfilename: str = typer.Option(
        Path.cwd() / "results.csv",
        help="The CSV file to hold the results. Defaults to 'results.csv' within the current working directory. Will overwrite any existing file of the same name.",
    ),
    algorithm: str = typer.Option("blake2b", help="The checksum algorithm to use."),
    recursive: bool = typer.Option(
        False,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Whether to scan directories recursively.",
    ),
):
    """Scan a directory, generate checksums for each file and store results in a CSV file.

    Args:
        input_path (str): The path containing files to be checked.
        csvfilename (str, optional): The CSV file to hold the results. Defaults to "results.csv" within the current working directory. Will overwrite any existing file of the same name.
        algorithm (str, optional): The checksum algorithm to use. Defaults to "blake2b".
        recursive (bool, optional): Whether to scan directories recursively. Defaults to False.
    """
    filelist = get_filelist(path=path, recursive=recursive)
    results = []
    if not filelist:
        print(f"The directory '{path}' does not exist.")
        return
    else:
        for file in track(filelist, description="Scanning ..."):
            results.append(
                {
                    "filename": str(file.resolve()),
                    "algorithm": algorithm,
                    "checksum": create_checksum(file, algorithm=algorithm),
                }
            )
        write_csv(csvfilename=csvfilename, results=results)


@app.command()
def check(
    path: str = typer.Argument(..., help="The path containing files to be checked."),
    csvfilename: str = typer.Argument(
        ..., help="The path containing files to be checked."
    ),
    algorithm: str = typer.Option("blake2b", help="The checksum algorithm to use."),
    recursive: bool = typer.Option(
        False,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Whether to scan directories recursively.",
    ),
):
    """Check a directory by comparing checksum results from a CSV file with newly generated checksums.

    Args:
        csvfilename (str): The CSV file containing checksum results for comparison.
        path (str): The path containing files to be checked.
        algorithm (str, optional): The checksum algorithm to use. Defaults to "blake2b".
        recursive (bool, optional): Whether to scan directories recursively. Defaults to False.
    """
    filelist = get_filelist(path=path, recursive=recursive)
    num_good = 0
    num_bad = 0
    total = 0
    if not filelist:
        print(f"The directory '{path}' does not exist.")
        return
    else:
        for file in track(filelist, description="Checking ..."):
            if check_file_against_csv(
                csvfilename=csvfilename,
                checkfilename=str(file.resolve()),
                algorithm=algorithm,
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
    results = scan(directory)
    print(results)
    csvfile = "/Users/cbunn/projects/checkr/results.csv"
    write_csv(csvfile, results)
    check(csvfilename=csvfile, path=directory)


if __name__ == "__main__":
    app()
