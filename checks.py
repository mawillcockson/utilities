# pylint: disable=inherit-non-class, too-few-public-methods
# pylint: disable=unsubscriptable-object
"""
Runs the checks for each repository
"""
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess  # pylint: disable=unused-import
from typing import List, NamedTuple, Optional

assert sys.version_info >= (3, 7), "Need Python 3.7+"


class CIFiles(NamedTuple):
    "all of the build files"
    checks: List[Path]


def in_git_dir(path: Path) -> bool:
    """
    check if a file or folder is under .git/

    This is a very cheap check, and won't catch symlinks or hardlinks, etc
    """
    return ".git" in path.parts


def find_ci_files(path: Path = Path(".")) -> CIFiles:
    "list all the python files used by the ci system"
    # List the check files
    check_files = [
        path for path in Path(".").glob("**/checks.py") if not in_git_dir(path)
    ]
    return CIFiles(checks=check_files)


def run_tool(
    args: List[str], cwd: Optional[Path] = None, check: bool = True
) -> "CompletedProcess[str]":
    "passes standard arguments to subprocess.run"
    print(f"exec> {' '.join(args)}")
    result = subprocess.run(
        args=args, cwd=cwd, capture_output=True, text=True, check=check
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result


def run_py(path: Path) -> None:
    "runs a .py file with python"
    assert path.is_file(), "path must be a file"
    assert path.suffix == ".py", "file must be a .py file"
    run_tool([sys.executable, str(path)], cwd=path.parent, check=False)


def run_checks(project_dir: Path) -> None:
    "runs the checks.py in a project directory"
    assert project_dir.is_dir(), "Project directory must be a directory"
    path = project_dir.resolve(strict=True)
    check_file = path / "checks.py"
    assert check_file.is_file(), "check file must be a file"
    run_py(path=check_file)


def sub_projects(path: Path = Path(".")) -> List[Path]:
    "list the project directories"
    project_directories = list()
    for item in path.glob("*"):
        if not in_git_dir(item) and item.is_dir():
            project_directories.append(item)

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

    # Install linting tools
    pipx_install(["isort"])
    pipx_install(["black"])
    pipx_install(["pylint"])
    pipx_install(["mypy"])

    # Find linting tool executables
    pipx_bin = Path("~/.local/bin").expanduser().resolve(strict=True)
    assert pipx_bin.is_dir(), "pipx_bin must be a directory"
    isort_exe = pipx_bin / "isort"
    black_exe = pipx_bin / "black"
    pylint_exe = pipx_bin / "pylint"
    mypy_exe = pipx_bin / "mypy"

    # Find mypy.ini
    mypy_ini = Path("./mypy.ini").resolve(strict=True)
    assert mypy_ini.is_file(), "mypy.ini must be a file"

    # Run tools
    for path in ci_files.checks:
        if not path.suffix == ".py":
            raise NotImplementedError("can only check .py files")

        assert path.is_file(), "paths must be files"
        assert path.suffix == ".py", "paths must be python files"
        run_tool(
            [str(isort_exe), "--profile=black", "--python-version=auto", str(path)]
        )
        run_tool([str(black_exe), str(path)])
        run_tool([str(pylint_exe), str(path)], cwd=path.parent)
        run_tool([str(mypy_exe), "--config-file", str(mypy_ini), str(path)])


def main() -> None:
    "main function that's run when this file is called as a script"
    for project_dir in sub_projects():
        run_checks(project_dir=project_dir)

    check_ci_files(ci_files=find_ci_files())


if __name__ == "__main__":
    main()