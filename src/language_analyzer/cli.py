"""Command-line interface for the language analyzer."""

from __future__ import annotations

import argparse
from collections import Counter
from io import TextIOWrapper
from typing import Any

from language_analyzer.analyzer import (
    analyze_dictionary,
    build_works_dataframe,
    compute_similarity,
    df_top_n,
    preprocess_and_tokenize,
)


def _write_stats(f: TextIOWrapper, stats: dict[str, Any], title: str) -> None:
    """Write a statistics block to the provided file object.

    Args:
        f: The open file object to write to.
        stats: A dictionary containing the standard text statistics
            (lines, words, etc.).
        title: The section header title to print above the statistics.
    """
    f.write(f"\n--- {title} ---\n")
    if "file_count" in stats:
        f.write(f"Number of files: {stats['file_count']}\n")
    f.write(f"Number of lines: {stats['lines_count']}\n")
    f.write(f"Number of words: {stats['words_count']}\n")
    f.write(f"Number of unique words: {stats['unique_words_count']}\n")

    f.write("Top 10 words:\n")
    for word, count in stats["top_10_words"]:
        f.write(f"  {word}: {count}\n")

    f.write("Letters counts:\n")
    for char, count in stats["letters_count"]:
        f.write(f"  {char}: {count}\n")

    f.write("Other characters counts:\n")
    for char, count in stats["other_count"]:
        f.write(f"  {char}: {count}\n")


def main() -> None:
    """Main entry point for the language-analyzer CLI.

    Parses arguments, runs dictionary and works analysis, and formats the output
    according to the specified report requirements.
    """
    parser = argparse.ArgumentParser(
        description="Language Analyzer for NPD Final Assignment"
    )
    parser.add_argument(
        "--dictionary", required=True, help="Path to the dictionary file"
    )
    parser.add_argument(
        "--dictionary-stats", action="store_true", help="Display global statistics"
    )
    parser.add_argument(
        "--works", required=True, help="Comma-separated paths to literary works"
    )
    parser.add_argument(
        "--no-words", action="store_true", help="List words not found in the dictionary"
    )
    parser.add_argument(
        "--frequencies", type=int, help="Top frequent words and similarity threshold"
    )
    parser.add_argument("--output", required=True, help="Output file for text report")
    parser.add_argument(
        "--replace", nargs="*", default=[], help="Character replacements like 'old:new'"
    )
    args = parser.parse_args()

    dict_stats, form_to_base = analyze_dictionary(args.dictionary)

    works_files = [w.strip() for w in args.works.split(",")]
    works_data: dict[str, list[str]] = {}
    works_stats: dict[str, dict[str, Any]] = {}

    total_letters_freq: Counter[str] = Counter()
    total_other_freq: Counter[str] = Counter()
    total_lines = 0

    for work in works_files:
        # Preprocess each literary work using the dictionary's mapping rules
        words, stats = preprocess_and_tokenize(work, args.replace, form_to_base)
        works_data[work] = words
        works_stats[work] = stats

        total_lines += stats["lines_count"]
        total_letters_freq.update(dict(stats["letters_count"]))
        total_other_freq.update(dict(stats["other_count"]))

    df = build_works_dataframe(works_data, form_to_base)

    with open(args.output, "w", encoding="utf-8") as out:
        # 1. Dictionary statistics
        if args.dictionary_stats:
            _write_stats(out, dict_stats, "Dictionary Statistics")

        # 2. Combined works statistics
        if args.dictionary_stats:
            letters = sorted(total_letters_freq.items(), key=lambda x: (-x[1], x[0]))
            other = sorted(total_other_freq.items(), key=lambda x: (-x[1], x[0]))
            total_stats = {
                "file_count": len(works_files),
                "lines_count": total_lines,
                "words_count": int(df["total_count"].sum()) if not df.empty else 0,
                "unique_words_count": len(df),
                "top_10_words": df_top_n(df, "total_count", 10),
                "letters_count": letters,
                "other_count": other,
            }
            _write_stats(out, total_stats, "Total Statistics for all Master files")

        # 3. Similarity comparison
        if args.frequencies is not None and len(works_files) > 1:
            n = args.frequencies
            out.write("\n--- Similarity Criterion (0..100) ---\n")
            for i, w1 in enumerate(works_files):
                for w2 in works_files[i + 1 :]:
                    sim = compute_similarity(df, w1, w2, n)
                    out.write(f"Similarity between {w1} and {w2}: {sim:.2f}\n")

        # 4. Separate works statistics
        if args.dictionary_stats and len(works_files) > 1:
            for work in works_files:
                _write_stats(out, works_stats[work], f"Statistics for file: {work}")

        # 5. Top frequent words
        if args.frequencies is not None:
            n = args.frequencies
            out.write(f"\n--- Top {n} frequent words ---\n")
            for work in works_files:
                top = df_top_n(df, work, n)
                out.write(f"\nFile: {work}\n")
                for word, count in top:
                    out.write(f"  {word}: {count}\n")

        # 6. Words not in dictionary
        if args.no_words:
            out.write("\n--- Words not in dictionary ---\n")
            if not df.empty:
                missing = df[~df["in_dictionary"]]
                if not missing.empty:
                    # Sort missing words by count descending, then alphabetically
                    missing_s = missing.loc[
                        missing["total_count"] > 0, "total_count"
                    ].reset_index()
                    if not missing_s.empty:
                        missing_s.columns = ["word", "count"]
                        missing_s = missing_s.sort_values(
                            by=["count", "word"], ascending=[False, True]
                        )
                        for _, row in missing_s.iterrows():
                            out.write(f"{row['word']}: {row['count']}\n")


if __name__ == "__main__":
    main()
