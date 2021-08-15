# standard library imports
from pathlib import Path

# third party imports
import yaml
import typer
from rich.console import Console
from rich.progress import track

# local imports
from helpers import start_logging, create_checksum, get_filelist
from models import database as db, csvfile as cf


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
# - DONE - Advanced: Add SQLAlchemy ORM in addition to a CSV file option
#           - DB is the default option
# - TODO - Advanced: Test multithreading/multiprocessing

app = typer.Typer(help="File Integrity Checker")


def scan_db(filename: str, algorithm: str) -> None:
    # check if there's already a result in the DB, and if so, update it
    if db.get_stored_checksum_from_db(checkfilename=filename, algorithm=algorithm):
        db.update_result_in_db(
            checkfilename=filename,
            checksum=create_checksum(filename, algorithm=algorithm),
            algorithm=algorithm,
        )
    # otherwise store the result normally
    else:
        db.store_result_in_db(
            checkfilename=filename,
            checksum=create_checksum(filename, algorithm=algorithm),
        )


@app.command()
def scan(
    paths: list[str] = typer.Option(
        [Path.cwd()],
        help="The paths containing files to be checked. Can be multiple.",
    ),
    csvfile: str = typer.Option(
        None,
        help="The CSV file to hold the results. A good location is '~/.checkr/results.csv'. When scanning, any existing file of the same name is overwritten.",
    ),
    usedb: bool = typer.Option(
        True,
        help="Whether to use a database to store results. Defaults to True. Set config in '.env' file.",
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
        help="A file to use as a log of operations. Defaults to '~/.checkr/checkr.log'.",
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
        usedb = config.get("usedb", usedb)
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

    if csvfile:
        csvfilepath = Path(csvfile).resolve()
    filelist = get_filelist(paths=paths, recursive=recursive)
    if filelist:
        for file in track(filelist, console=console, description="Scanning ..."):
            filename = str(file.resolve())
            logger.info(f"Scanning {filename}")
            # check if there's already a result in the DB, and if so, update it
            if usedb:
                scan_db(filename, algorithm)
            elif csvfile:
                # check if there's already a result in the CSV, and if so, update it
                if csvfilepath.is_file() and cf.get_stored_checksum_from_csv(
                    csvfilename=csvfilepath,
                    checkfilename=filename,
                    algorithm=algorithm,
                ):
                    cf.update_result_in_csv(
                        csvfilename=csvfilepath,
                        checkfilename=filename,
                        checksum=create_checksum(file, algorithm=algorithm),
                        algorithm=algorithm,
                    )
                # otherwise, store the file normally
                else:
                    cf.store_result_in_csv(
                        csvfilename=csvfilepath,
                        checkfilename=filename,
                        checksum=create_checksum(filename, algorithm=algorithm),
                        algorithm=algorithm,
                    )
            else:
                logger.warning("Neither a database or CSV file option chosen.")
                print("You must choose either to use a database or CSV file.")
                break
    logger.info("Scan complete.")


@app.command()
def check(
    paths: list[str] = typer.Option(
        [Path.cwd()],
        help="The paths containing files to be checked. Can be multiple.",
    ),
    csvfile: str = typer.Option(
        None,
        help="The CSV file holding results of a previous scan to check against. A good location is '~/.checkr/results.csv'.",
    ),
    usedb: bool = typer.Option(
        True,
        help="Whether to use a database for results. Defaults to True. Set config in '.env' file.",
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
        help="A file to use as a log of operations. Defaults to '~/.checkr/checkr.log'.",
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
        usedb = config.get("usedb", usedb)
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
            filename = str(file.resolve())
            logger.info(f"Checking {filename}")
            if usedb:
                if db.check_file_against_db(
                    checkfilename=filename, algorithm=algorithm
                ):
                    logger.info(f"File ({filename}) passed the check.")
                    num_good += 1
                else:
                    logger.warning(f"File ({filename}) FAILED the check.")
                    num_bad += 1
            elif csvfile:
                if cf.check_file_against_csv(
                    csvfile=csvfile,
                    checkfilename=str(file.resolve()),
                    algorithm=algorithm,
                ):
                    logger.info(f"File ({filename}) passed the check.")
                    num_good += 1
                else:
                    logger.warning(f"File ({filename}) FAILED the check.")
                    num_bad += 1
            else:
                logger.warning("Neither a database or CSV file option chosen.")
                print("You must choose either to use a database or CSV file.")
                break
            total += 1
        end_message = f"Check completed. {num_bad} files failed out of {total} total files checked."
        print(end_message)
        logger.info(end_message)


if __name__ == "__main__":
    app()
