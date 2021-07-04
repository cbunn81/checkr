import hashlib
from timeit import default_timer as timer


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
