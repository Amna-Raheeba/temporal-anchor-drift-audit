from temporal_anchor.cli import main


def test_cli_demo(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Strategy: note_date" in out
    assert "Strategy: oracle" in out


def test_cli_audit(capsys):
    assert main(["audit", "--cases", "5"]) == 0
    out = capsys.readouterr().out
    assert "section_aware" in out
    assert "MAE" in out


def test_cli_evaluate(capsys, tmp_path, monkeypatch):
    # evaluate writes into the package's results/ dir; just check the
    # console contract here (file outputs are covered by test_reproduce).
    assert main(["evaluate"]) == 0
    out = capsys.readouterr().out
    assert "Part 1 MAE" in out
    assert "Part 2 MAE" in out
