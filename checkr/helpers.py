# standard library imports
import hashlib
from pathlib import Path
import logging
import logging.handlers

# third party imports
from rich.logging import RichHandler


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
