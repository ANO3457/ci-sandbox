import pytest
from click.testing import CliRunner

from ci_sandbox.cli import cli
from ci_sandbox.matrix import expand_matrix


def invoke(tmp_path, matrix, *, event="push", condition=""):
    path = tmp_path / "matrix.yml"
    path.write_text(
        "name: Matrix\non: [push]\njobs:\n  test:\n"
        "    runs-on: ubuntu-latest\n"
        + (f"    if: '{condition}'\n" if condition else "")
        + "    strategy:\n      matrix:\n"
        + "\n".join("        " + line for line in matrix.splitlines())
        + "\n    steps:\n      - run: echo simulated\n"
        "  deploy:\n    needs: test\n    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    return CliRunner().invoke(cli, ["simulate", str(path), "--event", event])


def test_cli_shows_cartesian_combinations_and_counts(tmp_path):
    result = invoke(tmp_path, "node: [18, 20]\nos: [ubuntu, windows]")
    assert result.exit_code == 0, result.output
    for node in (18, 20):
        for os in ("ubuntu", "windows"):
            assert f"test (node={node}, os={os})" in result.output
    assert "5 success" in result.output
    assert "(5 jobs)" in result.output


def test_skipped_job_shows_every_combination_and_reason(tmp_path):
    result = invoke(tmp_path, "node: [18, 20]", condition="false")
    assert result.exit_code == 0, result.output
    assert "test (node=18) (condition: false)" in result.output
    assert "test (node=20) (condition: false)" in result.output
    assert "3 skipped" in result.output


def test_untriggered_event_displays_matrix_entries(tmp_path):
    result = invoke(tmp_path, "node: [18, 20]", event="release")
    assert result.exit_code == 0, result.output
    assert "test (node=18) (event 'release' does not trigger)" in result.output
    assert "test (node=20) (event 'release' does not trigger)" in result.output


def test_include_exclude_and_added_combinations(tmp_path):
    result = invoke(
        tmp_path,
        """node: [18, 20]
os: [ubuntu, windows]
exclude:
  - node: 18
    os: windows
include:
  - coverage: true
  - node: 20
    coverage: false
  - node: 22
    os: macos""",
    )
    assert result.exit_code == 0, result.output
    assert "test (node=18, os=windows" not in result.output
    assert "test (node=18, os=ubuntu, coverage=True)" in result.output
    assert "test (node=20, os=ubuntu, coverage=False)" in result.output
    assert "test (node=20, os=windows, coverage=False)" in result.output
    assert "test (node=22, os=macos)" in result.output
    assert "(5 jobs)" in result.output


def test_include_only_keeps_independent_rows(tmp_path):
    result = invoke(tmp_path, "include:\n  - node: 18\n  - node: 20")
    assert result.exit_code == 0, result.output
    assert "test (node=18)" in result.output
    assert "test (node=20)" in result.output
    assert "(3 jobs)" in result.output


def test_dynamic_matrix_reports_limitation_instead_of_fake_success(tmp_path):
    result = invoke(tmp_path, "node: ${{ fromJSON(inputs.nodes) }}")
    assert result.exit_code == 1
    assert "literal list" in result.output
    assert "Traceback" not in result.output


def test_include_does_not_merge_previously_added_rows_or_mutate_input():
    matrix = {"node": [18], "include": [{"node": 20}, {"node": 20, "os": "macos"}]}
    assert expand_matrix({"matrix": matrix}) == [
        {"node": 18},
        {"node": 20},
        {"node": 20, "os": "macos"},
    ]
    assert matrix["include"] == [{"node": 20}, {"node": 20, "os": "macos"}]


@pytest.mark.parametrize(
    "matrix",
    [
        "${{ inputs.matrix }}",
        {"node": []},
        {"node": [18], "include": ["bad"]},
        {"node": [18], "exclude": {}},
        {},
    ],
)
def test_invalid_or_dynamic_matrices_have_clear_errors(matrix):
    with pytest.raises(ValueError, match="matrix"):
        expand_matrix({"matrix": matrix})


def test_matrix_expansion_has_a_bound():
    with pytest.raises(ValueError, match="256"):
        expand_matrix({"matrix": {"node": list(range(257))}})


def test_exclude_matches_only_existing_keys_and_include_can_restore_row():
    assert expand_matrix({"matrix": {"node": [18], "exclude": [{"missing": None}]}}) == [
        {"node": 18}
    ]
    assert expand_matrix(
        {"matrix": {"node": [18], "exclude": [{"node": 18}], "include": [{"node": 18}]}}
    ) == [{"node": 18}]
