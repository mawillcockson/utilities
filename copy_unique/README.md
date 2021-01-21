# copy_unique

Copies unique files from one directory to another.

Uniqueness is determined by hashing.

This tool is incredibly slow. [`rsync`][] is a better tool.

## Installation

It's suggested to use [`pipx`][]:

```sh
python -m pip install --user --upgrade pip setuptools wheel pipx
python -m pipx ensurepath
python -m pipx install 'git+https://github.com/mawillcockson/utilities#egg=copy_unique&subdirectory=copy_unique'
```

Plain [`pip`][] should be:

```sh
python -m pip install --user --upgrade pip setuptools wheel
python -m pip install --user 'git+https://github.com/mawillcockson/utilities#egg=copy_unique&subdirectory=copy_unique'
```

[`rsync`]: <https://rsync.samba.org/> "rsync homepage"
[`pipx`]: <https://pipxproject.github.io/pipx/installation/> "pipx installation documentation"
[`pip`]: <https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support> "pip VCS url documentation"
