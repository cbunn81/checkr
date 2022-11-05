# checkr

![Example terminal execution](/checkr.gif "Example terminal execution")

checkr is a file integrity checker. It can scan a directory or list of directories, generating checksum digests for all files, and it can subsequently check those files to see if the checksum digests have changed, which would indicate either a modification or a corruption of the file.

There are two options for storage of the results: a database or a CSV file. By default, a database is used, but if you prefer you can set the appropriate options below to use a CSV file instead.

<br>

---

<br>

## Installation

### Clone the repo

```bash
git clone https://github.com/cbunn81/checkr.git
```

### Install the dependencies (preferably after creating a virtual environment)

```bash
pip install -r requirements.txt
```

### Rename the example config and env files

```bash
mv .env.example .env
mv config.yml.example config.yml
```

Then edit those files as shown below to suit your needs.

<br>

---

<br>

## Usage

### Quickstart

#### Scan a directory

```bash
python checkr scan /path/to/files
```

#### Check a directory

```bash
python checkr check /path/to/files
```

### Using a config file

All of the configuration options can be set using a config file, which has a YAML format. By default, `checkr` will look for a config file located at `~/.checkr/config.yml`. You can also set this on the command line when scanning or checking:

```bash
python checkr scan --config /path/to/config.yml
```

Included is an example of a config file you can use as a starting point (You can also find this file at `config.yml.example` in the repo root). Each argument/option is placed at the same level. Keep in mind that the paths to scan/check are set as a list of one or more strings. If you don't wish to override the default values for any of the options, remove the line from the config file completely.

```yaml
# Set paths as a list of those paths you wish to scan/check
paths:
  - /path/to/data1
  - /path/to/data2
  - /path/to/data3

# A flag to choose whether to use a database. Default is true.
usedb: True

# The CSV file to hold the results. Since a database is used by default,
# no default CSV file path is set. To override this behavior and use a
# CSV file, first set the above 'usedb' option to 'False' and then set
# a path to your CSV file below.
# NOTE: When scanning, any existing file of the same name is overwritten.
#csvfile: /path/to/results.csv

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

---

### Setting database environment variables

In order to use the database storage, you'll need to tell SQLAlchemy where to find your database. Use `.env.example` as a starting point and save your file as `.env`.

The simplest option is to use SQLite. To set the SQLite database file to the current directory:

```
SQLALCHEMY_DATABASE_URL = "sqlite:///checkr.sqlite"
```

You also need to set a location for the SQLAlchemy log file (make sure it's an absolute path):

```
SQLALCHEMY_LOG = "/path/to/sqlalchemy.log"
```

---

### Setting options on the command line

#### Use a database for storage (the default)

```bash
python checkr scan /path/to/scan --usedb
```

#### Set a CSV filename to use

If you wish to use a CSV file, instead of a database, try the following.

```bash
python checkr scan /path/to/scan --no-usedb --csvfilename /path/to/file.csv
```

#### Scan a directory recursively

```bash
python checkr scan -r /path/to/files
```

#### Scan multiple directories recursively

```bash
python checkr scan -r /path/to/files1 /path/to/files2 /path/to/files3
```

#### Check a directory

```bash
python checkr check /path/to/files
```

Or, if using a CSV file:

```bash
python checkr check /path/to/files --no-usedb --csvfilename /path/to/file.csv
```

#### Check a directory recursively

```bash
python checkr check -r /path/to/files
```

#### Check multiple directories recursively

```bash
python checkr check -r /path/to/files1 /path/to/files2 /path/to/files3
```

#### Set verbosity

By default, only ERROR-level statements are shown.

Set option once to show INFO-level statements.

```bash
python checkr check -v /path/to/files /path/to/file.csv
```

Set option twice to show DEBUG-level statements.

```bash
python checkr check -vv /path/to/files /path/to/file.csv
```

### Set a log file to use

By default, `checkr` creates a log file named `checkr.log` within `~/.checkr/` to log results of both scanning and checking so you don't need to log to the console every time. If you wish to use another file, please set it using the following example.

```bash
python checkr scan --log /path/to/logfile.log /path/to/files
```

### Select a checksum algorithm

By default, `blake2b` is used as it is more cryptographically secure while also being faster, but `md5` can also be selected.

```bash
python checkr scan --algorithm blake2b|md5 /path/to/files
```
