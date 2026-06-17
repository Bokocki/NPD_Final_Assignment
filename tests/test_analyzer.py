"""Tests for language analyzer core logic."""

from collections import Counter

import pandas as pd

from language_analyzer.analyzer import (
    analyze_dictionary,
    build_works_dataframe,
    compute_similarity,
    count_chars,
    df_top_n,
    preprocess_and_tokenize,
    top_n,
)

# ---------------------------------------------------------------------------
# count_chars
# ---------------------------------------------------------------------------


def test_count_chars_letters_merged():
    """Uppercase and lowercase should merge into one count."""
    letters, other = count_chars("AaB")
    letter_dict = dict(letters)
    assert letter_dict["a"] == 2
    assert letter_dict["b"] == 1
    assert other == []


def test_count_chars_excludes_whitespace():
    """Spaces, tabs, newlines should not appear in 'other'."""
    _, other = count_chars("a b\tc\n--'2")
    other_chars = {ch for ch, _ in other}
    assert " " not in other_chars
    assert "\t" not in other_chars
    assert "\n" not in other_chars


def test_count_chars_other_characters():
    """Punctuation and digits should appear in 'other'."""
    _, other = count_chars("a,b!c3")
    other_dict = dict(other)
    assert other_dict[","] == 1
    assert other_dict["!"] == 1
    assert other_dict["3"] == 1


def test_count_chars_empty():
    """Empty string should produce empty lists."""
    letters, other = count_chars("")
    assert letters == []
    assert other == []


# ---------------------------------------------------------------------------
# top_n
# ---------------------------------------------------------------------------


def test_top_n_basic():
    freq = Counter({"a": 10, "b": 5, "c": 5, "d": 2, "e": 5})
    res1 = top_n(freq, 1)
    assert res1 == [("a", 10)]

    res2 = top_n(freq, 2)
    assert len(res2) == 4
    assert ("a", 10) in res2
    assert ("b", 5) in res2
    assert ("c", 5) in res2
    assert ("e", 5) in res2


def test_top_n_empty():
    assert top_n(Counter(), 5) == []


# ---------------------------------------------------------------------------
# build_works_dataframe
# ---------------------------------------------------------------------------


def test_build_works_dataframe():
    works_data = {
        "work1": ["apple", "banana", "apple", "cherry"],
        "work2": ["banana", "date", "date"],
    }
    form_to_base = {
        "apple": "apple",
        "banana": "banana",
        "cherry": "cherry",
        "date": "date",
    }

    df = build_works_dataframe(works_data, form_to_base)

    assert df.shape == (4, 4)
    assert df.loc["apple", "work1"] == 2
    assert df.loc["apple", "work2"] == 0
    assert df.loc["banana", "total_count"] == 2
    assert df.loc["date", "in_dictionary"]


def test_build_works_dataframe_empty():
    """Empty works dict should produce an empty DataFrame with expected columns."""
    df = build_works_dataframe({}, {})
    assert df.empty
    assert "total_count" in df.columns
    assert "in_dictionary" in df.columns


# ---------------------------------------------------------------------------
# df_top_n
# ---------------------------------------------------------------------------


def test_df_top_n():
    data = {"total_count": [10, 5, 5, 2, 5]}
    df = pd.DataFrame(data, index=["a", "b", "c", "d", "e"])

    res1 = df_top_n(df, "total_count", 1)
    assert res1 == [("a", 10)]

    res2 = df_top_n(df, "total_count", 2)
    assert res2 == [("a", 10), ("b", 5), ("c", 5), ("e", 5)]


def test_df_top_n_missing_column():
    df = pd.DataFrame({"x": [1, 2]})
    assert df_top_n(df, "nonexistent", 5) == []


# ---------------------------------------------------------------------------
# compute_similarity
# ---------------------------------------------------------------------------


def test_compute_similarity_identical():
    """Two works with identical top words should have 100% Jaccard."""
    data = {"work1": [10, 5, 2], "work2": [8, 6, 1]}
    df = pd.DataFrame(data, index=["a", "b", "c"])
    assert compute_similarity(df, "work1", "work2", 2) == 100.0


def test_compute_similarity_jaccard():
    """Verify true Jaccard: |intersection| / |union| * 100."""
    data = {"work1": [10, 5, 2, 0], "work2": [0, 6, 0, 8]}
    df = pd.DataFrame(data, index=["a", "b", "c", "d"])
    # top 2 of work1: {a, b}, top 2 of work2: {d, b}
    # intersection = {b}, union = {a, b, d}
    # Jaccard = 1/3 * 100 ≈ 33.33
    sim = compute_similarity(df, "work1", "work2", 2)
    assert abs(sim - 100 / 3) < 0.01


def test_compute_similarity_no_overlap():
    data = {"work1": [10, 0], "work2": [0, 8]}
    df = pd.DataFrame(data, index=["a", "b"])
    assert compute_similarity(df, "work1", "work2", 1) == 0.0


# ---------------------------------------------------------------------------
# preprocess_and_tokenize
# ---------------------------------------------------------------------------


def test_preprocess_and_tokenize(tmp_path):
    d = tmp_path / "dummy.txt"
    d.write_text(
        "Tést filé with string-string and punctuátion! And words. And éé.\n",
        encoding="utf-8",
    )

    replacements = ["é:e", "á:a"]
    form_to_base = {"test": "test_base", "string-string": "string_base"}

    words, stats = preprocess_and_tokenize(str(d), replacements, form_to_base)

    assert "test_base" in words
    assert "file" in words
    assert "punctuation" in words
    assert "string_base" in words
    assert "ee" in words
    assert stats["unique_words_count"] == 8
    assert stats["lines_count"] == 1
    assert stats["words_count"] == 10


def test_preprocess_and_tokenize_empty(tmp_path):
    """An empty file should produce zero words and empty stats."""
    d = tmp_path / "empty.txt"
    d.write_text("", encoding="utf-8")
    words, stats = preprocess_and_tokenize(str(d), [], {})
    assert words == []
    assert stats["words_count"] == 0
    assert stats["unique_words_count"] == 0


# ---------------------------------------------------------------------------
# analyze_dictionary
# ---------------------------------------------------------------------------


def test_analyze_dictionary(tmp_path):
    dict_file = tmp_path / "dict.txt"
    dict_file.write_text(
        "kot, kota, kotu\nKot, Kota, Kotu\npies, psa, psu\n"
        "acid jazz, acid jazzach\na priori, a\nbad-word!, bad\n"
        "drzewo, drzewa, zły znak, drzewu\n",
        encoding="utf-8",
    )

    stats, form_to_base = analyze_dictionary(str(dict_file))

    assert stats["lines_count"] == 7
    # Uppercase duplicated lines are filtered
    assert stats["unique_words_count"] == 6

    # Valid unfiltered global words: 16 total
    assert stats["words_count"] == 16

    # Mapping logic assertions remain the same (filtered)
    assert "bad" not in form_to_base
    assert "acid" not in form_to_base
    assert "jazz" not in form_to_base
    assert "priori" not in form_to_base
    assert "a" not in form_to_base
    assert "zły znak" not in form_to_base

    assert form_to_base["kota"] == "kot"
    assert form_to_base["drzewa"] == "drzewo"
    assert form_to_base["drzewu"] == "drzewo"
