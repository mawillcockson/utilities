# guestfs_generator

This utility is purely about generating a static package index that's [PEP 503][] compatible for [libguestfs's Python bindings package, `guestfs`][guestfs-index].

It uses [`dumb-pypi`][] for the generation.

## Explanation

Currently, `guestfs` [is not on PyPI][]. This does not mean it's not installable, it just has to be installed from its index. Python's built-in `pip` can do this:

```sh
python -m pip install --find-links 'http://download.libguestfs.org/python#egg=guestfs' \
    --trusted-host 'download.libguestfs.org' \
    guestfs
```

_Note: the `guestfs` package is a C-extension that requires compilation in order to be able to be installed_

Other package managers that don't support a `--find-links`-style behaviour can usually still use these packages, however a direct link to the `.tar.gz` file has to be used instead, which makes it more difficult to automatically use newer releases.

This tool parses the [current index][guestfs-index] and uses [`dumb-pypi`][] to build a set of static files that can be served over HTTPS to other package managers that support specifying additional indeces for certain packages.

Thanks to [this issue comment][] for pointing me towards this solution.

[PEP 503]: <https://www.python.org/dev/peps/pep-0503/> "PEP 503"
[guestfs-index]: <https://download.libguestfs.org/python/> "index of guestfs packages"
[`dumb-pypi`]: <https://github.com/chriskuehl/dumb-pypi> "dumb-pypi on GitHub"
[is not on PyPI]: <https://pypi.org/project/guestfs> "where guestfs would be if it were on PyPI"
[this issue comment]: <https://github.com/python-poetry/poetry/issues/1391#issuecomment-600135563> "issue comment that inspired this"
