# GitHub Actions

Notes on the GitHub Actions in this repository.

## Check

Linting and type checking should occur on every push and pull request, but should not cause the push to fail.

On the branch `main` it should cause the merge to fail if it doesn't succeed.

## Build

Build should happen in response to pull requests being opened, and releases being created.

### Pull Requests

Should trigger a build that uploads the build artefact as a comment.

## Releases

A release should be created in response to a tag being added. The tag must meet the following criteria:

- Be an annotated tag (required for attaching messages and PGP signatures)
- Have a name that matches the [semantic versioning conventions][semver]
- Point to a commit on the `main` branch
- Have a valid PGP signature

In that case, a release should be created that summarizes the changes, includes the tag message, and triggers the release build so build artefacts can be included.

To facilitate automatic changelog generation, merges to `main` should check to make sure the commit message follows the [convential commits][] format.

[semver]: <https://semver.org/> "Semantic Versioning Specification Homepage"
[conventional commits]: <https://www.conventionalcommits.org/en/v1.0.0/> "Conventional Commits Specification Homepage"
