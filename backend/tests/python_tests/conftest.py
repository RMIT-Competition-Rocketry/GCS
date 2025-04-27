import pytest  # type: ignore
from click.testing import CliRunner


@pytest.fixture
def runner():
    """
    Provides a Click CliRunner for invoking commands in tests.
    """
    return CliRunner()


@pytest.fixture(autouse=True)
def isolate_fs(tmp_path, monkeypatch):
    """
    Automatically run each test in an isolated temporary directory.

    - tmp_path: a pathlib.Path to a unique temporary directory
    - monkeypatch.chdir: switch cwd to that temp dir
    """
    monkeypatch.chdir(tmp_path)
    yield
    # any cleanup goes here
