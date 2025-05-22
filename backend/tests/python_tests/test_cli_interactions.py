from click.testing import CliRunner
import rocket
import pytest


@pytest.mark.dependency(name="test_cli_help")
def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(rocket.cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.dependency(depends=["test_cli_help"])
@pytest.mark.dependency(name="test_cli_dev_help")
def test_cli_dev_help():
    runner = CliRunner()
    result = runner.invoke(rocket.dev, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.dependency(depends=["test_cli_help"])
@pytest.mark.dependency(name="test_cli_run_help")
def test_cli_run_help():
    runner = CliRunner()
    result = runner.invoke(rocket.run, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.dependency(depends=["test_cli_help"])
@pytest.mark.dependency(name="test_cli_sim_help")
def test_cli_sim_help():
    runner = CliRunner()
    result = runner.invoke(rocket.simulation, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
