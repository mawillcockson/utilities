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

## Use

In your dependency management tool of choice, there should be a way to provide another package index.

The package index is currently published to:

<https://mawillcockson.github.io/utilities/guestfs_index/simple/>

For example, `pip` has the [`--extra-index-url`][] option:

```sh
python -m pip install --extra-index-url https://mawillcockson.github.io/utilities/guestfs_index/simple/
```

For [`poetry`][], add a [`[[tool.poetry.source]]` section to `pyproject.toml`][poetry-extra-source]:

```toml
[[tool.poetry.source]]
name = "guestfs"
url = "https://mawillcockson.github.io/utilities/guestfs_index/simple/"
secondary = true
```

It's very important that the entire url be entered correctly. Some tools behave strangely if, for instance, the slash at the end is left off.

## How to regenerate the `guestfs` index

If the index available at <https://mawillcockson.github.io/utilities/guestfs_index/simple/> is not up to date with the source index at <https://download.libguestfs.org/python/>, then leave a comment on [issue #4][] with the exact text below:

```
Please update the guestfs index.
```

It's very important that the comment contain only that text, and nothing else.

This will cause the [`guestfs_index.yaml`][] workflow to be run, which will hopefully update the package index in a few minutes.

If the index is not updated, or the workflow fails in another way, please open a new issue. Please do not leave a comment on #4.

[PEP 503]: <https://www.python.org/dev/peps/pep-0503/> "PEP 503"
[guestfs-index]: <https://download.libguestfs.org/python/> "index of guestfs packages"
[`dumb-pypi`]: <https://github.com/chriskuehl/dumb-pypi> "dumb-pypi on GitHub"
[is not on PyPI]: <https://pypi.org/project/guestfs> "where guestfs would be if it were on PyPI"
[this issue comment]: <https://github.com/python-poetry/poetry/issues/1391#issuecomment-600135563> "issue comment that inspired this"
[`--extra-index-url`]: <https://pip.pypa.io/en/stable/reference/pip_install/#install-extra-index-url> "documentation on pip's --extra-index-url option"
[`guestfs_index.yaml`]: <https://github.com/mawillcockson/utilities/blob/main/.github/workflows/guestfs_index.yaml> "The guestfs_index workflow file for GitHub Actions"
[`poetry`]: <https://python-poetry.org/> "Main python poetry website"
[poetry-extra-source]: <https://python-poetry.org/docs/repositories/#install-dependencies-from-a-private-repository> "Explanation of how to add addition sources in poetry"
[issue #4]: <https://github.com/mawillcockson/utilities/issues/4> "Issue #4"
