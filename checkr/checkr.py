# standard library imports
import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
import csv
import logging
import logging.handlers

# third party imports
import yaml
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import track


# To do list
# - DONE - Basic: Run checksum on a directory of files
# - DONE - Basic: Store checksums and filenames in a CSV text file
# - DONE - Basic: Run checksums and compare to those stored
# - DONE - Intermediate: Integrate Typer
# - DONE - Intermediate: Make input directory a command argument
# - DONE - Intermediate: Make output file a command argument
# - DONE - Intermediate: Log errors to a file and stdout
# - DONE - Intermediate: Display progress bar
# - DONE - Intermediate: Allow for levels of verbosity in output
# - DONE - Intermediate: Make hash algorithm a command argument
# - DONE - Intermediate: Allow for a list of input directories
# - Done - Intermediate: Allow for a config file to set command arguments
# - TODO - Intermediate: Allow for command line arguments to override config file
#           - won't work easily with default values for options in command definition
#           - consider removing default values and having default config file instead
# - DONE - Intermediate: Use RichHandler to solve progress bar redirection issue
# - DONE - Intermediate: Rotate log files
# - TODO - Advanced: Switch to SQLAlchemy ORM instead of CSV files
#           - OR have both as options?
# - TODO - Advanced: Test multithreading/multiprocessing

app = typer.Typer(help="File Integrity Checker")


def start_logging(
    console: object,
    file_level: str = "DEBUG",
    console_level: str = "ERROR",
    filename: str = Path.cwd() / "checkr.log",
) -> object:
    """Create a logger and initialize both logging to a file and to the console.

    Args:
        file_level (str): Logging level for the file handler
        console_level (str): Logging level for the console handler
        filename (str): Filename to store the file handler log output
    """
    fh_loglevel = getattr(logging, file_level.upper(), None)
    if not isinstance(fh_loglevel, int):
        raise ValueError(f"Invalid log level: {file_level}")
    ch_loglevel = getattr(logging, console_level.upper(), None)
    if not isinstance(ch_loglevel, int):
        raise ValueError(f"Invalid log level: {console_level}")
    logger = logging.getLogger("checkr")
    # set a default log level threshold
    logger.setLevel(logging.DEBUG)
    # create file handler
    filepath = Path(filename).resolve()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        filename=filepath, maxBytes=1_048_576, backupCount=5
    )
    fh.setLevel(level=fh_loglevel)
    # create console handler using RichHandler so progress bar is redirected
    ch = RichHandler(console=console)
    ch.setLevel(level=ch_loglevel)
    fh.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    ch.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    # add the handlers to logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


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
    filepath = Path(csvfilename).resolve()
    with open(filepath, newline="") as csvfile:
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


def get_filelist(paths: list[str], recursive: bool = False) -> list[str]:
    """Get a list of files (but not directories) from a path.

    Args:
        paths (list[str]): The path(s) to search for files.
        recursive (bool, optional): Whether to recursively search the path. Defaults to False.

    Returns:
        list[str]: A list of all filenames, given as absolute paths.
    """
    logger = logging.getLogger("checkr")
    filelist = []
    for path in paths:
        dir = Path(path)
        if not dir.exists():
            logger.error(f"The directory '{dir}' does not exist.")
        elif not dir.is_dir():
            logger.error(f"'{dir}' is not a directory.")
        else:
            results = dir.rglob("*") if recursive else dir.glob("*")
            filelist.extend([x for x in results if x.is_file()])
    return filelist


@app.command()
def scan(
    paths: list[str] = typer.Option(
        [Path.cwd()],
        help="The paths containing files to be checked. Can be multiple.",
    ),
    csvfile: str = typer.Option(
        Path.home() / ".checkr/results.csv",
        help="The CSV file to hold the results. Defaults to '~/.checkr/results.csv'. When scanning, any existing file of the same name is overwritten.",
    ),
    algorithm: str = typer.Option("blake2b", help="The checksum algorithm to use."),
    recursive: bool = typer.Option(
        False,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Whether to scan directories recursively.",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        min=0,
        max=2,
        clamp=True,
        help="The verbosity level. Once for INFO and twice for DEBUG.",
    ),
    configfile: str = typer.Option(
        Path.home() / ".checkr/config.yml",
        "--config",
        "-c",
        help="A YAML config file holding values for all above options and arguments. Entries in config file override command line arguments.",
    ),
    logfile: str = typer.Option(
        Path.home() / ".checkr/checkr.log",
        "--log",
        "-l",
        help="A file to use as a log of operations.",
    ),
):
    """
    Scan a directory or directories, generate checksums for each file and store results in a CSV file.
    """
    try:
        # Read config file and set variables, using command line versions as fallbacks
        with open(Path(configfile).resolve()) as cf_file:
            config = yaml.safe_load(cf_file.read())
        paths = config.get("paths", paths)
        csvfile = config.get("csvfile", csvfile)
        algorithm = config.get("algorithm", algorithm)
        recursive = config.get("recursive", recursive)
        verbose = config.get("verbose", verbose)
        logfile = config.get("logfile", logfile)
    except FileNotFoundError:
        print("No config file found.")

    if verbose == 0:
        loglevel = "ERROR"
    elif verbose == 1:
        loglevel = "INFO"
    else:
        loglevel = "DEBUG"
    # set a Rich console to use for both logging and progress bar output
    console = Console(stderr=True)
    logger = start_logging(console_level=loglevel, filename=logfile, console=console)

    csvfilepath = Path(csvfile).resolve()
    filelist = get_filelist(paths=paths, recursive=recursive)
    if filelist:
        for file in track(filelist, console=console, description="Scanning ..."):
            logger.info(f"Scanning {file.resolve()}")
            # TODO - check if there's already a result in the CSV, and if so, update it
            if csvfilepath.is_file() and get_stored_checksum_from_csv(
                csvfilename=csvfilepath,
                checkfilename=str(file.resolve()),
                algorithm=algorithm,
            ):
                update_result_in_csv(
                    csvfilename=csvfilepath,
                    checkfilename=file.resolve(),
                    checksum=create_checksum(file, algorithm=algorithm),
                    algorithm=algorithm,
                )
            else:
                store_result_in_csv(
                    csvfilename=csvfilepath,
                    checkfilename=file.resolve(),
                    checksum=create_checksum(file, algorithm=algorithm),
                    algorithm=algorithm,
                )

    logger.info("Scan complete.")


@app.command()
def check(
    paths: list[str] = typer.Option(
        [Path.cwd()],
        help="The paths containing files to be checked. Can be multiple.",
    ),
    csvfile: str = typer.Option(
        Path.home() / ".checkr/results.csv",
        help="The CSV file holding results of a previous scan to check against. Defaults to '~/.checkr/results.csv'.",
    ),
    algorithm: str = typer.Option("blake2b", help="The checksum algorithm to use."),
    recursive: bool = typer.Option(
        False,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Whether to scan directories recursively.",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        min=0,
        max=2,
        clamp=True,
        help="The verbosity level. Once for INFO and twice for DEBUG.",
    ),
    configfile: str = typer.Option(
        Path.home() / ".checkr/config.yml",
        "--config",
        "-c",
        help="A YAML config file holding values for all above options and arguments. Entries in config file override command line arguments.",
    ),
    logfile: str = typer.Option(
        Path.home() / ".checkr/checkr.log",
        "--log",
        "-l",
        help="A file to use as a log of operations.",
    ),
):
    """
    Check a directory or directories by comparing checksum results from a CSV file with newly generated checksums.
    """
    try:
        # Read config file and set variables, using command line versions as fallbacks
        with open(Path(configfile).resolve()) as cf_file:
            config = yaml.safe_load(cf_file.read())
        paths = config.get("paths", paths)
        csvfile = config.get("csvfile", csvfile)
        algorithm = config.get("algorithm", algorithm)
        recursive = config.get("recursive", recursive)
        verbose = config.get("verbose", verbose)
        logfile = config.get("logfile", logfile)
    except FileNotFoundError:
        print("No config file found.")

    if verbose == 0:
        loglevel = "ERROR"
    elif verbose == 1:
        loglevel = "INFO"
    else:
        loglevel = "DEBUG"
    # set a Rich console to use for both logging and progress bar output
    console = Console(stderr=True)
    logger = start_logging(console_level=loglevel, filename=logfile, console=console)

    filelist = get_filelist(paths=paths, recursive=recursive)
    num_good = 0
    num_bad = 0
    total = 0
    if filelist:
        for file in track(filelist, console=console, description="Checking ..."):
            logger.info(f"Checking {file.resolve()}")
            if check_file_against_csv(
                csvfile=csvfile,
                checkfilename=str(file.resolve()),
                algorithm=algorithm,
            ):
                logger.info(f"File ({file.resolve()}) passed the check.")
                num_good += 1
            else:
                logger.warning(f"File ({file.resolve()}) FAILED the check.")
                num_bad += 1
            total += 1
        end_message = f"Check completed. {num_bad} files failed out of {total} total files checked."
        print(end_message)
        logger.info(end_message)


def main():
    directory = "/Users/cbunn/projects/checkr/data/"
    results = scan(directory)
    print(results)
    csvfile = "/Users/cbunn/projects/checkr/results.csv"
    write_csv(csvfile, results)
    check(csvfile=csvfile, path=directory)


if __name__ == "__main__":
    app()
