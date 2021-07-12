# checkr

checkr is a file integrity checker. It can scan a directory, generating checksum digests for all files, and it can subsequently check those files to see if the checksum digests have changed, which would indicate either a modification or a corruption of the file.

## Usage

### Scan a directory:

```bash
python checkr scan <path>
```

### Scan a directory recursively:

```bash
python checkr scan -r <path>
```

### Check a directory:

```bash
python checkr check <path> <csvfile>
```

### Check a directory recursively:

```bash
python checkr check -r <path> <csvfile>
```
