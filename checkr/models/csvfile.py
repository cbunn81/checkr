# standard library imports
from pathlib import Path
from tempfile import NamedTemporaryFile
import csv
import logging

# local imports
from helpers import create_checksum


def write_csv(filename: str, results: list[dict]):
    """Create a CSV file and write the checksum results to it.

    Args:
        filename (str): The file to create.
        results (list[dict]): A list of results to write to the CSV file. Each result is a dictionary with keys: filename, algorithm, checksum.
    """
    filepath = Path(filename).resolve()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as csvfile:
        fieldnames = list(results[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def store_result_in_csv(
    csvfilename: str, checkfilename: str, checksum: str, algorithm: str = "blake2b"
) -> None:
    """Store a checksum result in a given csvfile, creating the file if needed.

    Args:
        csvfilename (str): The CSV file to use or create.
        checkfilename (str): The file that was checked.
        checksum (str): The checksum result for the file.
        algorithm (str, optional): The checksum algorithm used. Defaults to "blake2b".
    """
    logger = logging.getLogger("checkr")
    csvfilepath = Path(csvfilename).resolve()
    csvfilepath.parent.mkdir(parents=True, exist_ok=True)
    checkfilepath = Path(checkfilename).resolve()
    checkfilepath.parent.mkdir(parents=True, exist_ok=True)
    # check if the CSV file already exists
    file_exists = csvfilepath.is_file()
    with open(csvfilepath, "a", newline="") as csvfile:
        fieldnames = ["filename", "algorithm", "checksum"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # write the header if this is a new file to be created
        if not file_exists:
            writer.writeheader()
            logger.info(f"File {csvfilename} doesn't exist. Creating.")
        writer.writerow(
            {"filename": checkfilepath, "algorithm": algorithm, "checksum": checksum}
        )


def update_result_in_csv(
    csvfilename: str, checkfilename: str, checksum: str, algorithm: str = "blake2b"
) -> None:
    """Update an existing result in a CSV file.

    Args:
        csvfilename (str): The CSV file holding the results.
        checkfilename (str): The file that was checked.
        checksum (str): The checksum result for the file.
        algorithm (str, optional): The checksum algorithm used. Defaults to "blake2b".
    """
    logger = logging.getLogger("checkr")
    tempfile = NamedTemporaryFile(mode="w", delete=False)
    tempfilepath = Path(tempfile.name).resolve()
    filepath = Path(csvfilename).resolve()
    with open(filepath, "r", newline="") as csvfile, tempfile:
        fieldnames = ["filename", "algorithm", "checksum"]
        reader = csv.DictReader(csvfile)
        writer = csv.DictWriter(tempfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            if (
                row["filename"].strip() == str(checkfilename).strip()
                and row["algorithm"].strip() == algorithm.strip()
            ):
                logger.info(f"Updating stored record for file {checkfilename}.")
                row["checksum"] = checksum
            row = {
                "filename": row["filename"],
                "algorithm": row["algorithm"],
                "checksum": row["checksum"],
            }
            writer.writerow(row)
    tempfilepath.replace(filepath)


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
    csvfilepath = Path(csvfilename).resolve()
    with open(csvfilepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["filename"] == checkfilename and row["algorithm"] == algorithm:
                return row["checksum"]


def check_file_against_csv(
    csvfile: str, checkfilename: str, algorithm: str = "blake2b"
) -> bool:
    """Compare a previously generated checksum from a CSV file with a newly generated one.

    Args:
        csvfile (str): The CSV file containing the previously generated checksum.
        checkfilename (str): The file to check.
        algorithm (str, optional): The checksum algorithm to use. Defaults to "blake2b".

    Returns:
        bool: True if the checksums match, otherwise False.
    """
    logger = logging.getLogger("checkr")
    stored_checksum = get_stored_checksum_from_csv(
        csvfilename=csvfile, checkfilename=checkfilename, algorithm=algorithm
    )
    if stored_checksum is not None:
        new_checksum = create_checksum(filename=checkfilename, algorithm=algorithm)
        if stored_checksum == new_checksum:
            return True
        else:
            return False
    else:
        logger.warning(
            f"No checksum exists for file ({checkfilename}) in CSV file ({csvfile})."
        )
