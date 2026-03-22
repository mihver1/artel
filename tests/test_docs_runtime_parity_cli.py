from click.testing import CliRunner


def test_web_help_marks_surface_experimental():
    from artel_core import cli as cli_mod

    runner = CliRunner()
    result = runner.invoke(cli_mod.cli, ["web", "--help"])

    assert result.exit_code == 0
    assert "experimental NiceGUI-based Artel web UI" in result.output
    assert "web UI unavailable in this checkout" not in result.output


def test_top_level_help_advertises_experimental_web_surface():
    from artel_core import cli as cli_mod

    runner = CliRunner()
    result = runner.invoke(cli_mod.cli, ["--help"])

    assert result.exit_code == 0
    assert "Start the experimental Artel web UI." in result.output
    assert "Reserved web command; unavailable in this checkout." not in result.output
