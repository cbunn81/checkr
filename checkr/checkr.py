import hashlib
from timeit import default_timer as timer
from pathlib import Path


# To do list
# - DONE - Basic: Run checksum on a directory of files
# - TODO - Basic: Store checksums and filenames in a CSV text file
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


def checkfiles(input_path: str):
    dir = Path(input_path)
    if not dir.exists():
        print(f"The directory '{dir}' does not exist.")
    elif not dir.is_dir():
        print(f"'{dir}' is not a directory.")
    else:
        filelist = dir.glob("*")
        for file in filelist:
            print(file)
            print(blake2b(file))


def main():
    directory = "/Users/cbunn/projects/checkr/data/"
    checkfiles(directory)

    # start_md5 = timer()
    # file_hash = md5(filename=filename)
    # end_md5 = timer()
    # print(type(file_hash))
    # print(file_hash)
    # print("MD5 completed in ")
    # print(end_md5 - start_md5)

    # filename = "/Users/cbunn/projects/checkr/data/D3S_24191.NEF"
    # existing_blake2b_hash = "63aca612bf686aaa34847d381a047eb4c7d096284ec2aabe80218149f85b457871f2758b6d6b0edfc6534a9c16e90ce3875182a219e4bc7120870ce508347c11"
    # new_blake2b_hash = blake2b(filename=filename)
    # if existing_blake2b_hash == new_blake2b_hash:
    #     print("Hashes match!")
    # else:
    #     print("Hashes DON'T match!")
    # start_blake2b = timer()
    # file_hash = blake2b(filename=filename)
    # end_blake2b = timer()
    # print(type(file_hash))
    # print(file_hash)
    # print("Blake2b completed in ")
    # print(end_blake2b - start_blake2b)


if __name__ == "__main__":
    main()
