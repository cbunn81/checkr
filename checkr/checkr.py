import hashlib
from timeit import default_timer as timer


# To do list
# - TODO - Basic: Run checksum on a directory of files
# - TODO - Basic: Store checksums and filenames in a CSV text file
# - TODO - Basic: Run checksums and compare to those stored
# - TODO - Intermediate: Integrate Typer
# - TODO - Intermediate: Make directory a command argument
# - TODO - Intermediate: Log errors to a file and stdout
# - TODO - Intermediate: Display progress bar
# - TODO - Intermediate: Allow for levels of verbosity in output
# - TODO - Intermediate: Make hash algorithm a command argument
# - TODO - Advanced: Switch to SQLAlchemy ORM instead of CSV files


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


filename = "/Users/cbunn/projects/checkr/data/D3S_24191.NEF"
start_md5 = timer()
file_hash = md5(filename=filename)
end_md5 = timer()
print(type(file_hash))
print(file_hash)
print("MD5 completed in ")
print(end_md5 - start_md5)

start_blake2b = timer()
file_hash = blake2b(filename=filename)
end_blake2b = timer()
print(type(file_hash))
print(file_hash)
print("Blake2b completed in ")
print(end_blake2b - start_blake2b)
