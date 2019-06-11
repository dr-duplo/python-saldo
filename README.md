# Saldo (python-saldo)

Saldo is a simple python3 tool to view bank account balances and transactions using
the FinTS standard. The data is synced from the bank and stored in an encrypted database
in the users home folder. The password can be provided or it will be randomly chosen.
If a keyring is available it will be used to store the password for convenience. 

The user is able to assign categories (labels) to transactions to group them. The labeling can
be done automatically when enough manual labels are provided by the user.

The tool can be used via a CLI or a GTK application.

## Command Line Interface

The package installs a script called 'saldo'. Use '--help' to see commands and options.
This works with all commands

```bash
Usage: saldo [OPTIONS] COMMAND [ARGS]...

Options:
  --db PATH            Database file name
  --db-password TEXT   Database file password
  -v, --verbosity LVL  Either CRITICAL, ERROR, WARNING, INFO or DEBUG
  --help               Show this message and exit.

Commands:
  accounts      Show and manage accounts.
  balances      Show balances.
  fetch         Fetch and update account data.
  gui           Start graphical user interface.
  tags          Show and manage transaction tags.
  transactions  Show transactions.
```

To add an account use:

```bash
saldo accounts add
```

and follow the instructions.

To fetch account balances and transactions use:

```bash
saldo fetch
```

To show transactions of the current month execute:
```bash
saldo transactions
```
To show current balances use:
```bash
saldo balances
```

## GUI Application

The GUI is based on GTK and designed to be a GNOME application. Currently this part of saldo is
under heavy development and must be used with care. The gui can be started using:

```bash
saldo gui
```

The package also installs a *.desktop file which provides the start icon on your desktop. 

## Installation

Due to the non-existing official release you have to clone this repo and install the package manually with:

```bash
git clone https://github.com/dr-duplo/python-saldo.git
cd python-saldo
python3 -m pip install -r requirements.txt
python3 setup.py install
```

To use the encrypted sqlite database you may have to take additional installation steps upfront.

### Install pysqlcipher3 Dependencies
Install via package manager of your distro like:
```bash
sudo apt install python3-dev libsqlcipher-dev
```

## Development

### History
The predecessor of Saldo is a C++ GTK application with the same name which used AqBanking as HBCI
client. This turned out to be unstable and outdated, so I decided to switch to a python3 implementation.
Luckily the python-fints and mt-940 projects came across to enable this. 

### Current State and Participation
Due to the roots of the tool, some design decisions may seam strange, but this could be changed.
The tool is unfinished and unstable. Nevertheless I use it on a daily basis with joy. If you find it 
useful, too, please contribute!

### Known Issues
- Transaction sync does not fully handle edge cases and quirks of banks. This will get better
  if the tool has broader usage and more issues arise
- Documentation missing
- GUI is far from complete and concept is not finished
- Database structure may need a rework
- No unit tests 
  
## Tasks / Roadmap
- Design and implement account balance forecast
- Investigate performance of automatic labeling and tweak it afterwards
- Command Line Interface
    - Manage accounts (delete, change)
- GUI application
    - Finish GUI concept
    - Implement account management
    - Finish monthly transaction analysis
    - Finish fractional labeling
- Packaging
- Initial Release

## Acknowledgements

Special thanks go to these projects:  
- [python-fints](https://github.com/raphaelm/python-fints)
- [mt-940](https://github.com/WoLpH/mt940)
