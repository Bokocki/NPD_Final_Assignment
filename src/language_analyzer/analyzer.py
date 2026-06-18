"""Core analysis logic for the language analyzer, built on pandas."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

import pandas as pd

from language_analyzer.constants import POLISH_LETTERS, PUNCT_FILTER


def _sort_key(x: tuple[str, int]) -> tuple[int, str]:
    """Sort key for character frequency: descending count, ascending char.

    Args:
        x: A tuple of (character, count).

    Returns:
        A tuple of (-count, character) for proper sorting.
    """
    return (-x[1], x[0])


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def count_chars(text: str) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Count characters in the provided text.

    Letters are merged to lowercase. Whitespace is excluded from the "other" category.

    Args:
        text: The raw text string to analyze.

    Returns:
        A tuple containing two lists:
        - The first list contains tuples of (Polish letter, count), sorted descending
            by count then ascending alphabetically.
        - The second list contains tuples of (other char, count), sorted descending by
            count then ascending alphabetically.
    """
    freq = Counter(text)
    letters: Counter[str] = Counter()

    for ch, n in freq.items():
        if ch.lower() in POLISH_LETTERS:
            letters[ch.lower()] += n

    other = {
        ch: n
        for ch, n in freq.items()
        if ch.lower() not in POLISH_LETTERS and not ch.isspace()
    }

    return sorted(letters.items(), key=_sort_key), sorted(other.items(), key=_sort_key)


def top_n(freq: Counter[str], n: int) -> list[tuple[str, int]]:
    """Return the top *n* items from a Counter with tie-inclusive cut-off.

    Args:
        freq: A Counter object containing item frequencies.
        n: The number of top items to retrieve.

    Returns:
        A list of (item, count) tuples, sorted by count descending, then alphabetically.
        Includes all ties at the boundary threshold.
    """
    if not freq:
        return []

    items = sorted(freq.items(), key=_sort_key)
    if len(items) <= n:
        return items

    threshold = items[n - 1][1]
    return [it for it in items if it[1] >= threshold]


def df_top_n(df: pd.DataFrame, col: str, n: int) -> list[tuple[str, int]]:
    """Return the top *n* words from a DataFrame column with tie-inclusive cut-off.

    Args:
        df: The pandas DataFrame containing word counts.
        col: The column name representing the specific work's counts.
        n: The number of top words to retrieve.

    Returns:
        A list of (word, count) tuples, sorted by count descending, then alphabetically.
        Includes all ties at the boundary threshold.
    """
    if df.empty or col not in df.columns:
        return []

    s = df.loc[df[col] > 0, col]
    if s.empty:
        return []

    s_top = s.nlargest(n, keep="all")
    df_top = s_top.reset_index()

    word_col, count_col = df_top.columns[0], df_top.columns[1]
    df_top = df_top.sort_values(by=[count_col, word_col], ascending=[False, True])

    return list(zip(df_top[word_col], df_top[count_col], strict=True))


# ---------------------------------------------------------------------------
# Dictionary analysis
# ---------------------------------------------------------------------------


def analyze_dictionary(dict_path: str) -> tuple[dict[str, Any], dict[str, str]]:
    """Analyze the dictionary file and generate statistics and word mappings.

    - Raw character/line counts come from the unaltered file.
    - Word statistics come from lowercased, deduplicated lines.
    - The mapping dictionary filters lines/words containing punctuation or whitespace.

    Args:
        dict_path: The file path to the dictionary text file.

    Returns:
        A tuple containing:
        - A dictionary with calculated statistics (lines, words, chars, top words).
        - A mapping of conjugated forms to their base form.
    """
    with open(dict_path, encoding="utf-8") as fh:
        raw = fh.read()

    raw_lines = raw.splitlines()
    # Note: Character counts include raw delimiters (e.g., commas)
    letters_sorted, other_sorted = count_chars(raw)

    # Lowercase, deduplicate, and sort for deterministic processing order
    # Code after `if` strips whitespace, lowercases, and evaluates to False if empty
    unique_lines = sorted({ln for line in raw_lines if (ln := line.strip().lower())})

    # Process stats and collect mappings in a single loop
    all_unique_words: set[str] = set()
    base_to_conjugations: dict[str, set[str]] = {}

    form_to_base: dict[str, str] = {}

    for line in unique_lines:
        parts = [w.strip() for w in line.split(",") if w.strip()]
        if not parts:
            continue

        base = parts[0]

        # --- 1. STATS LOGIC (unfiltered) ---
        if base not in base_to_conjugations:
            base_to_conjugations[base] = set()

        for w in parts:
            all_unique_words.add(w)
            base_to_conjugations[base].add(w)

        # --- 2. MAPPING LOGIC (filtered) ---
        # Discard line for mapping if base word has punctuation or whitespace
        if any(ch in PUNCT_FILTER for ch in base) or any(ch.isspace() for ch in base):
            continue

        # Explicitly lock-in base word to map to itself
        form_to_base[base] = base

        # Map to base form only words without punctuation or whitespace
        for w in parts[1:]:
            if (
                w not in form_to_base
                and not any(ch in PUNCT_FILTER for ch in w)
                and not any(ch.isspace() for ch in w)
            ):
                form_to_base[w] = base

    base_conjugations_counts = Counter(
        {base: len(conjs) for base, conjs in base_to_conjugations.items()}
    )

    stats = {
        "lines_count": len(raw_lines),
        "words_count": len(all_unique_words),
        "unique_words_count": len(base_to_conjugations),
        "top_10_words": top_n(base_conjugations_counts, 10),
        "letters_count": letters_sorted,
        "other_count": other_sorted,
    }

    return stats, form_to_base


# ---------------------------------------------------------------------------
# Work tokenization
# ---------------------------------------------------------------------------

# Compiled regex patterns (compiled once at module level)
_RE_HYPHEN_PROTECT = re.compile(r"(?<=\w)-(?=\w)")
_RE_PUNCT_STRIP = re.compile(r"[^\w\s]")


def preprocess_and_tokenize(
    file_path: str,
    replacements: list[str],
    form_to_base: dict[str, str],
) -> tuple[list[str], dict[str, Any]]:
    """Read a literary work, tokenize it, and map tokens to base forms.

    Character statistics are computed from the unaltered file before replacements.

    Args:
        file_path: The file path to the literary work text file.
        replacements: A list of string replacements formatted as 'old:new'.
        form_to_base: A dictionary mapping conjugated words to their base forms.

    Returns:
        A tuple containing:
        - A list of processed tokens from the file.
        - A dictionary containing file statistics.
    """
    with open(file_path, encoding="utf-8") as fh:
        raw = fh.read()

    lines_count = raw.count("\n")
    # Account for a final line that might not end with a newline character
    if raw and not raw.endswith("\n"):
        lines_count += 1

    # Note: Character statistics are derived from the raw file content, so punctuation
    # stripped later will still be reflected in the "other" character counts.
    letters_sorted, other_sorted = count_chars(raw)

    # Apply user-specified replacements (format: 'old:new'), then lowercase
    content = raw
    for rep in replacements:
        if ":" in rep:
            # Split only on the first colon to allow for 'old:n:ew'
            old, new = rep.split(":", 1)
            content = content.replace(old, new)

    content = content.lower()

    # Tokenize: protect intra-word hyphens, strip remaining punctuation, restore hyphens
    content = _RE_HYPHEN_PROTECT.sub("___HYPHEN___", content)
    content = _RE_PUNCT_STRIP.sub(" ", content)
    content = content.replace("___HYPHEN___", "-").replace("_", " ")

    raw_tokens = content.split()

    # Map each token to its base form (identity if not in dictionary)
    words = [form_to_base.get(w, w) for w in raw_tokens]
    word_counts = Counter(words)

    stats = {
        "lines_count": lines_count,
        "words_count": len(words),
        "unique_words_count": len(word_counts),
        "top_10_words": top_n(word_counts, 10),
        "letters_count": letters_sorted,
        "other_count": other_sorted,
    }

    return words, stats


# ---------------------------------------------------------------------------
# DataFrame aggregation
# ---------------------------------------------------------------------------


def build_works_dataframe(
    works_data: dict[str, list[str]],
    form_to_base: dict[str, str],
) -> pd.DataFrame:
    """Build a word-frequency DataFrame across all provided literary works.

    Args:
        works_data: A mapping of work names to their respective list of tokens.
        form_to_base: The dictionary mapping conjugations to base forms.

    Returns:
        A pandas DataFrame where each row is a unique word and columns represent
        the occurrence counts per work, a total count, and a boolean dictionary check.
    """
    counters = {work: Counter(words) for work, words in works_data.items()}
    df = pd.DataFrame(counters).fillna(0).astype(int)

    if df.empty:
        return df.assign(
            total_count=pd.Series(dtype=int),
            in_dictionary=pd.Series(dtype=bool),
        )

    base_set = frozenset(form_to_base.values())
    return df.assign(
        total_count=df.sum(axis=1),
        in_dictionary=df.index.isin(form_to_base) | df.index.isin(base_set),
    )


def compute_similarity(df: pd.DataFrame, work1: str, work2: str, n: int) -> float:
    """Compute the Jaccard similarity (0-100) of the top-n words between two works.

    Jaccard index = |A n B| / |A u B|, scaled to a percentage between 0 and 100.
    Note: The top-n sets may contain more than n words due to tie-inclusive cut-offs,
    so the denominator utilizes the actual size of the resulting union.

    Args:
        df: The pandas DataFrame containing word counts per work.
        work1: The column name representing the first work.
        work2: The column name representing the second work.
        n: The number of top words to extract per work before comparison.

    Returns:
        A float representing the Jaccard similarity percentage (0.0 to 100.0).
    """
    top1 = {w for w, _ in df_top_n(df, work1, n)}
    top2 = {w for w, _ in df_top_n(df, work2, n)}

    if not top1 and not top2:
        return 100.0

    return len(top1 & top2) / len(top1 | top2) * 100.0
