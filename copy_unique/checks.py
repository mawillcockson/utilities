# pylint: disable=unsubscriptable-object, inherit-non-class
# pylint: disable=too-many-arguments, too-few-public-methods
"""
runs all the checks

this assumes that this file is located in the project directory

The general workflow is:

- Make sure pyenv is installed
- Find the currently supported versions of Python 3.7+ from pyenv install --list
- Install those versions, and the other needed versions
- pyenv local supported-cpython
- Make sure poetry is installed
- Run `poetry install --verbose --no-interaction` to install the project and
  dependencies using the system python version
- Run tox for tests
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess  # pylint: disable=unused-import
from typing import Dict, List, Mapping, NamedTuple, Optional, Tuple, cast
from warnings import warn

PYENV_INSTALL_SCRIPT_URL = (
    "https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer"
)
PYENV_WIN_RELEASES_URL = "https://api.github.com/repos/pyenv-win/pyenv-win/releases"
PYENV_WIN_REPO_URL = "https://github.com/pyenv-win/pyenv-win.git"
cpython_version_re = re.compile(
    r"^\s*(?P<major>2|3)\.(?P<minor>\d)\.(?P<micro>\d+)\s*$"
)


ReleasesJson = List[Dict[str, str]]


class CPythonVersion(NamedTuple):
    "CPython interpreter version specifier"
    major: int
    minor: int
    micro: int


def run(
    args: List[str],
    input_to_stdin: Optional[str] = None,
    cwd: Optional[Path] = None,
    check: bool = True,
    print_stdout: bool = True,
    env: Optional[Mapping[str, str]] = None,
) -> "CompletedProcess[str]":
    "run subprocess.run with common arguments"
    print(f"exec> {' '.join(args)}")
    if cwd:
        print(f"in: {cwd}")

    result = subprocess.run(
        args=args,
        input=input_to_stdin,
        cwd=cwd,
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if print_stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if check and result.returncode != 0:
        raise ValueError("process returned non-zero exit status")

    return result


def check_present(command_name: str, strict: bool = False) -> Optional[Path]:
    "check if a command is available"
    print(f"checking for '{command_name}'")
    path = which(command_name)
    if path is None and strict:
        raise FileNotFoundError(f"No command '{command_name}' found")

    if path is None:
        return None

    return Path(path).resolve(strict=True)


def pyenv_check_and_update() -> None:
    "run pyenv-doctor to make sure all the build requirements exist"
    run(["pyenv", "doctor"])
    run(["pyenv", "update"])


def add_to_github_path(path: Path) -> None:
    "if running on a GitHub Actions runner, persist path across steps"
    # NOTE:CI the GITHUB_PATH environment variable points to a file that is
    # read bottom to top to build the PATH environment variable for subsequent
    # actions
    # From:
    # https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-commands-for-github-actions#adding-a-system-path
    github_path = os.getenv("GITHUB_PATH", default=None)
    if not github_path:
        # The "GITHUB_PATH" environment variable only exists in GitHub Actions
        # runners
        return

    print(f"adding '{path}' for GITUB_PATH")
    with open(github_path, mode="a") as file:
        file.write(str(path.resolve(strict=True)))


def add_to_path(path: Path) -> None:
    "prepend a path to PATH"
    absolute_path = path.resolve(strict=True)
    current_path = os.environ["PATH"]
    if str(absolute_path) not in current_path.split(sep=os.pathsep):
        print(f"adding '{absolute_path}' to $PATH")
        os.environ["PATH"] = os.pathsep.join((str(absolute_path), current_path))
    add_to_github_path(absolute_path)
    bashrc = Path("~/.bashrc").expanduser().resolve()
    if not bashrc.is_file():
        return

    bashrc_text = bashrc.read_text()
    if str(absolute_path) in bashrc_text:
        return

    with bashrc.open(mode="a") as file:
        print(f"adding '{absolute_path}' to ~/.bashrc")
        bash_path = os.pathsep.join((str(absolute_path), "${PATH}"))
        file.write(f'export PATH="{bash_path}"')


def add_pyenv_to_path(pyenv_root: Path) -> None:
    "add pyenv executables and shims to the PATH"
    pyenv_shims = pyenv_root / "shims"
    try:
        pyenv_shims.mkdir()
    except FileExistsError:
        pass
    pyenv_bin = pyenv_root / "bin"
    # Add in reverse order so shims come first, just like how pyenv-installer
    # and "pyenv init -" set it up
    add_to_path(pyenv_bin)
    add_to_path(pyenv_shims)


def install_pyenv_linux() -> None:
    """
    These install steps are followed from:
    https://github.com/pyenv/pyenv-installer#install
    """
    # Check if pyenv is already installed
    pyenv_path = check_present("pyenv")
    if pyenv_path:
        warn("pyenv already installed")
        pyenv_check_and_update()
        return

    pyenv_root = Path().home().resolve(strict=True) / ".pyenv"

    if pyenv_root.exists() and not pyenv_root.is_dir():
        raise FileExistsError(f"'{pyenv_root}' already exists, but is not a directory")

    if pyenv_root.is_dir():
        warn("pyenv not added to path")
    else:
        print("installing pyenv...")
        # Make sure git, bash, and curl are installed
        check_present("git", strict=True)
        check_present("bash", strict=True)
        check_present("curl", strict=True)

        # pylint: disable=line-too-long

        # Download installer script
        script = run(
            ["curl", "-L", "--output", "-", PYENV_INSTALL_SCRIPT_URL],
            print_stdout=False,
        ).stdout
        if not script:
            sys.exit("No pyenv script returned????")

        # Run bash with the install script
        run(["bash"], input_to_stdin=script)

    add_pyenv_to_path(pyenv_root=pyenv_root)
    pyenv_check_and_update()


def install_pyenv_windows() -> None:
    """
    These install steps are taken from:
    https://github.com/pyenv-win/pyenv-win#installation
    """
    powershell_exe = str(check_present("powershell", strict=True))
    pyenv_win_releases_raw = run(
        ["curl", "-L", "--output", "-", PYENV_WIN_RELEASES_URL], print_stdout=False
    ).stdout
    json_error_msg = "Problem with decoding GittHub release data for pyenv-win"
    try:
        pyenv_win_releases: ReleasesJson = cast(
            ReleasesJson, json.loads(pyenv_win_releases_raw)
        )
    except json.decoder.JSONDecodeError as err:
        raise ValueError(json_error_msg) from err

    if not pyenv_win_releases:
        raise ValueError(json_error_msg)

    latest_release_data = pyenv_win_releases[0]
    # NOTE:BUG none of the linters, including mypy, caught the fact that the
    # commented line produces the following error:
    # TypeError: dict.get() takes no keyword arguments
    # 
    # latest_release_tag = latest_release_data.get("tag_name", default=None)
    latest_release_tag = latest_release_data.get("tag_name", None)
    if not latest_release_tag:
        raise ValueError(json_error_msg)

    run(
        [
            powershell_exe,
            "-C",
            (
                "git clone "
                "--depth 1"
                f"--branch {latest_release_tag}"
                f"{PYENV_WIN_REPO_URL}"
                '"$HOME/.pyenv"'
            ),
        ]
    )

    pyenv_win_root = r'"\.pyenv\pyenv-win\"'
    user = '"User"'
    run(
        [
            powershell_exe,
            (
                "[System.Environment]::SetEnvironmentVariable("
                "'PYENV',"
                f"$env:USERPROFILE + {pyenv_win_root},{user}"
                ")"
            ),
        ]
    )

    pyenv_win_bin = r'"\.pyenv\pyenv-win\bin;"'
    pyenv_win_shims = r'"\.pyenv\pyenv-win\shims;"'
    run(
        [
            powershell_exe,
            "-C",
            (
                "[System.Environment]::SetEnvironmentVariable("
                "'path',"
                f"$HOME + {pyenv_win_bin} + "
                f"$HOME + {pyenv_win_shims} + $env:Path,"
                f"{user}"
                ")"
            ),
        ]
    )

    pyenv_check_and_update()


def pyenv_stable_cpython() -> List[str]:
    """
    list the latest stable CPython versions in each branch, formatted for pyenv

    from:
    https://devguide.python.org/#status-of-python-branches
    """
    stable_branch_tuples = [(3, 6), (3, 7), (3, 8), (3, 9)]
    available_versions_text = run(
        ["pyenv", "install", "--list"], print_stdout=False
    ).stdout
    if not available_versions_text:
        raise ValueError("'pyenv install --list' returned nothing???")

    available_versions = [line.strip() for line in available_versions_text.splitlines()]
    available_cpython_versions = filter(
        None, map(cpython_version_re.match, available_versions)
    )

    available_cpython_version_tuples: List[CPythonVersion] = []
    for match in available_cpython_versions:
        cpython_version = CPythonVersion(
            major=int(match["major"]),
            minor=int(match["minor"]),
            micro=int(match["micro"]),
        )
        available_cpython_version_tuples.append(cpython_version)

    available_stable_cpython_versions: Dict[Tuple[int, int], List[CPythonVersion]] = {
        branch_tuple: [] for branch_tuple in stable_branch_tuples
    }
    for branch_tuple in available_stable_cpython_versions:
        versions_in_branch = sorted(
            version
            for version in available_cpython_version_tuples
            if version[:2] == branch_tuple
        )
        available_stable_cpython_versions[branch_tuple].extend(versions_in_branch)

    if not all(map(len, available_stable_cpython_versions.values())):
        raise ValueError(
            "a stable branch doesn't have any versions available:\n"
            f"{available_stable_cpython_versions}"
        )

    def max_version(versions: List[CPythonVersion]) -> Tuple[int, int, int]:
        "find the most recent version in each supported branch"
        return max((v.major, v.minor, v.micro) for v in versions)

    supported_cpython_versions = sorted(
        map(max_version, available_stable_cpython_versions.values()), reverse=True
    )

    return [
        ".".join(map(str, tuple(version))) for version in supported_cpython_versions
    ]


def pip_install(args: List[str]) -> None:
    "run pip install with the specified arguments"
    run([sys.executable, "-m", "pip", "install", "--user", "--upgrade"] + args)


def pipx_install(args: List[str]) -> None:
    "run pipx install with the specified arguments"
    run([sys.executable, "-m", "pipx", "install"] + args)


def install_poetry() -> None:
    "install poetry tool from https://python-poetry.org"
    if check_present("poetry", strict=False):
        warn("poetry already installed")
    else:
        # Upgrade pip
        pip_install("pip setuptools wheel".split())
        pip_install(["pipx"])
        pipx_install(["poetry"])
        run([sys.executable, "-m", "pipx", "ensurepath"], check=False)
        pipx_shims = (Path().home() / ".local" / "bin").resolve(strict=True)
        # Add pipx shims to PATH
        add_to_path(pipx_shims)
        assert check_present("poetry", strict=False), "pipx paths not configured"

    # NOTE: On some installations, poetry had to be run by absolute path
    poetry_exe = check_present("poetry")
    assert poetry_exe  # for mypy
    add_to_path(poetry_exe)


def pyenv_install(versions: List[str]) -> None:
    "run pyenv install with the correct options for each version"
    for version in versions:
        run(["pyenv", "install", "--skip-existing", version])


def main() -> None:
    "run main checks and tests, but no official builds"
    # Install pyenv for the appropriate platform
    if sys.platform in ["linux", "freebsd12"]:
        install_pyenv_linux()
    elif sys.platform in ["win32"]:
        install_pyenv_windows()
    else:
        raise NotImplementedError(f"not implemented for platform '{sys.platform}'")

    pyenv_root = Path(run(["pyenv", "root"]).stdout.strip()).resolve(strict=True)

    # Install necessary python versions
    recent_stable_cpython = [
        version for version in pyenv_stable_cpython() if not version.startswith("3.6")
    ]
    pyenv_install(["3.8.5", "3.7.3"] + recent_stable_cpython)
    run(["pyenv", "local"] + recent_stable_cpython)

    # Install poetry
    install_poetry()
    # Install project dependencies
    run(["poetry", "env", "use", sys.executable])
    run(["poetry", "install", "--no-interaction", "--verbose"])
    env = os.environ.copy()
    env.update({"PYENV_ROOT": str(pyenv_root), "TOX_PARALLEL_NO_SPINNER": "1"})
    run(
        ["poetry", "run", "tox"],
        env=env,
    )


if __name__ == "__main__":
    main()
