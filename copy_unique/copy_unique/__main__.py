"""
This is the file that python runs when this package is run as a module:
https://docs.python.org/3.6/using/cmdline.html#cmdoption-m

python -m copy_unique

It runs the main command-line interface
"""
from .main import main

if __name__ == "__main__":
    main()
