# Development Notes

Notes by the developer, for the developer.

## Layout

This is a mono repo with each subfolder of the main repo dedicated to a single utility or tool.

## Setting up for development

The only tool so far (`copy_unique`) uses [`poetry`][]. With that installed [following the instructions from the docs][poetry-install], clone the repository, and from the particular tool directory, run:

```sh
poetry install
poetry run tox
```

If that succeeds, develop away!

## Branching Strategy

Commits to `main` can only be made through pull request, and pull requests and
commits to `main` _must_ pass all checks.

Each tool has its own branch, with `feature/...` branches made off of those for
adding features and other tools.

[`poetry`]: <https://github.com/python-poetry/poetry> "poetry on GitHub"
[poetry-install]: <https://python-poetry.org/docs/#installation> "Installation in poetry's documentation"
