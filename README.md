# checkr

checkr is a file integrity checker. It can scan a directory or list of directories, generating checksum digests for all files, and it can subsequently check those files to see if the checksum digests have changed, which would indicate either a modification or a corruption of the file.

## Usage

### Scan a directory

```bash
python checkr scan /path/to/scan
```

### Set a CSV filename to use

By default, `checkr` creates a file named `results.csv` within `~/.checkr/` to hold the results of the scan. If you wish to use another file, please set it using the following example.

```bash
python checkr scan /path/to/scan --csvfilename /path/to/file.csv
```

### Scan a directory recursively

```bash
python checkr scan -r /path/to/scan
```

### Scan multiple directories recursively

```bash
python checkr scan -r /path/to/scan1 /path/to/scan2 /path/to/scan3
```

### Check a directory

The CSV file holding the results of a previous scan must be listed as an argument, unless the default file at `~/.checkr/results.csv` exists.

```bash
python checkr check /path/to/check /path/to/file.csv
```

### Check a directory recursively

```bash
python checkr check -r /path/to/check /path/to/file.csv
```

### Check multiple directories recursively

```bash
python checkr check -r /path/to/check1 /path/to/check2 /path/to/check3 /path/to/file.csv
```

### Set verbosity

#### By default, only ERROR-level statements are shown

#### Set option once to show INFO-level statements

```bash
python checkr check -v /path/to/check /path/to/file.csv
```

#### Set option twice to show DEBUG-level statements

```bash
python checkr check -vv /path/to/check /path/to/file.csv
```

### Set a log file to use

By default, `checkr` creates a log file named `checkr.log` within `~/.checkr/` to log results of both scanning and checking so you don't need to log to the console every time. If you wish to use another file, please set it using the following example.

```bash
python checkr scan --log /path/to/logfile.log /path/to/scan
```

### Select a checksum algorithm

By default, `blake2b` is used as it is more cryptographically secure while also being faster, but `md5` can also be selected.

```bash
python checkr scan --algorithm blake2b|md5 /path/to/scan
```

### Using a config file

All of the above configuration arguments can also be placed in a config file, using a YAML format. By default, `checkr` will look for a config file located at `~/.checkr/config.yml`. You can also set this on the command line when scanning or checking:

```bash
python checkr scan --config /path/to/config.yml
```

Included is an example of a config file you can use as a starting point. Each argument/option is placed at the same level. Keep in mind that the paths to scan/check are set as a list of one or more strings. If you don't wish to override the default values for any of the options, remove the line from the config file completely.

```yaml
# Set paths as a list of those paths you wish to scan/check
paths:
  - /path/to/data1
  - /path/to/data2
  - /path/to/data3

# The CSV file to hold the results. Defaults to '~/.checkr/results.csv'.
# When scanning, any existing file of the same name is overwritten.
csvfile: /path/to/results.csv

# A file to log operations. Defaults to '~/.checkr/checkr.log'. It logs
#  at DEBUG level and appends messages instead of overwriting.
logfile: /path/to/checkr.log

# For the checksum algorithm, you can choose either 'blake2b' or 'md5'.
# blake2b is recommended as it is more cryptographically secure and faster.
algorithm: blake2b

# By default, the scanning and checking functions do not recurse into
#  subdirectories. Set this to 'True' to recurse.
recursive: True

# Setting the verbosity to 0 means only ERROR-level messages will print.
# Setting it to 1 means only INFO-level and above messages will print.
# Setting it to 2 means only DEBUG-level and above messages will print.
verbose: 0
```
