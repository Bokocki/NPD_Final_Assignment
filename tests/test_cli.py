"""Tests for language analyzer CLI."""

import sys

from language_analyzer.cli import main


def test_main(tmp_path, monkeypatch):
    dict_file = tmp_path / "dict.txt"
    dict_file.write_text("kot, kota, kotu\npies, psa, psu\n", encoding="utf-8")

    work_file = tmp_path / "work.txt"
    work_file.write_text("Kot poszedł po psa. Kot ucieka.", encoding="utf-8")

    out_file = tmp_path / "out.txt"

    test_args = [
        "language_analyzer",
        "--dictionary",
        str(dict_file),
        "--dictionary-stats",
        "--works",
        str(work_file),
        "--no-words",
        "--frequencies",
        "5",
        "--output",
        str(out_file),
        "--replace",
        "po:do",
    ]

    monkeypatch.setattr(sys, "argv", test_args)
    main()

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")

    assert "Dictionary Statistics" in content
    assert "Statistics for all Master files" in content
    assert "Words not in dictionary" in content
    assert "doszedł" in content
    assert "Top 5 frequent words" in content
    assert "kot" in content
    assert "pies" in content
