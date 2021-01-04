# pylint: disable=inherit-non-class, too-few-public-methods
# pylint: disable=unsubscriptable-object
"""
Runs the checks for each repository
"""
import os
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess  # pylint: disable=unused-import
from typing import List, NamedTuple, Optional

assert sys.version_info >= (3, 7), f"Need Python 3.7+; got {sys.version}"


class CIFiles(NamedTuple):
    "all of the build files"
    checks: List[Path]


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


def in_git_dir(path: Path) -> bool:
    """
    check if a file or folder is under .git/

    This is a very cheap check, and won't catch symlinks or hardlinks, etc
    """
    return ".git" in path.parts


def find_ci_files(repository_path: Path = Path(".")) -> CIFiles:
    "list all the python files used by the ci system"
    path = repository_path.resolve(strict=True)
    # List the check files
    checks_files = [
        checks_file
        for checks_file in path.glob("**/checks.py")
        if not in_git_dir(checks_file)
    ]
    return CIFiles(checks=checks_files)


def run_tool(
    args: List[str], cwd: Optional[Path] = None, check: bool = True
) -> "CompletedProcess[str]":
    "passes standard arguments to subprocess.run"
    print(f"exec> {' '.join(args)}")
    if cwd:
        print(f"in: {cwd}")
    result = subprocess.run(
        args=args, cwd=cwd, capture_output=True, text=True, check=False, timeout=120
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if check and result.returncode != 0:
        raise ValueError("process returned non-zero exit code")

    return result


def run_py(path: Path) -> None:
    "runs a .py file with python"
    assert path.is_file(), f"'{path}' must be a file"
    assert path.suffix == ".py", f"'{path}' must be a .py file"
    run_tool([sys.executable, str(path)], cwd=path.parent, check=False)


def run_checks(project_dir: Path) -> None:
    "runs the checks.py in a project directory"
    assert (
        project_dir.is_dir()
    ), f"Project directory '{project_dir}' must be a directory"
    path = project_dir.resolve(strict=True)
    check_file = path / "checks.py"
    assert check_file.is_file(), f"check file '{check_file}' must be a file"
    run_py(path=check_file)


def sub_projects(path: Path = Path(".")) -> List[Path]:
    "list the project directories"
    project_directories = list()
    for item in path.glob("*"):
        if not in_git_dir(item) and item.is_dir() and not item.name.startswith("."):
            project_directories.append(item.resolve(strict=True))

    return project_directories


def run_pip(args: List[str]) -> None:
    "runs pip with the specified arguments"
    run_tool([sys.executable, "-m", "pip"] + args)


def pipx_install(args: List[str]) -> None:
    "run pipx install with the specified arguments"
    run_tool([sys.executable, "-m", "pipx", "install"] + args)


def check_ci_files(ci_files: CIFiles) -> None:
    "lints and type checks all of the CI files"
    # Upgrade pip
    run_pip("install --user --upgrade pip setuptools wheel".split())

    # Install pipx
    run_pip("install --user --upgrade pipx".split())
    run_tool([sys.executable, "-m", "pipx", "ensurepath"])

    # Install linting tools
    pipx_install(["isort"])
    pipx_install(["black"])
    pipx_install(["pylint"])
    pipx_install(["mypy"])

    # Find linting tool executables
    pipx_bin = (Path().home() / ".local/bin").resolve(strict=True)
    add_to_path(pipx_bin)
    assert pipx_bin.is_dir(), f"'{pipx_bin}' must be a directory"
    isort_exe = pipx_bin / "isort"
    black_exe = pipx_bin / "black"
    pylint_exe = pipx_bin / "pylint"
    mypy_exe = pipx_bin / "mypy"

    # Find mypy.ini
    mypy_ini = Path("./mypy.ini").resolve(strict=True)
    assert mypy_ini.is_file(), f"'{mypy_ini}' must be a file"

    # Run tools
    for path in ci_files.checks:
        if not path.suffix == ".py":
            raise NotImplementedError("can only check .py files")

        assert path.is_file(), f"'{path}' must be file"
        assert path.suffix == ".py", f"'{path}' must be python file"
        run_tool(
            [
                str(isort_exe),
                "--profile=black",
                "--python-version=auto",
                "--check",
                str(path),
            ]
        )
        run_tool([str(black_exe), "--check", str(path)])
        run_tool([str(pylint_exe), str(path.name)], cwd=path.parent)
        run_tool([str(mypy_exe), "--config-file", str(mypy_ini), str(path)])


def main() -> None:
    "main function that's run when this file is called as a script"
    for project_dir in sub_projects():
        run_checks(project_dir=project_dir)

    check_ci_files(ci_files=find_ci_files())


if __name__ == "__main__":
    main()
