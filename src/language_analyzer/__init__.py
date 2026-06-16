"""Language Analyzer — literary text analysis library."""

__version__ = "0.1.0"

from language_analyzer.analyzer import (
    analyze_dictionary,
    build_works_dataframe,
    compute_similarity,
    count_chars,
    df_top_n,
    preprocess_and_tokenize,
    top_n,
)

__all__ = [
    "analyze_dictionary",
    "build_works_dataframe",
    "compute_similarity",
    "count_chars",
    "df_top_n",
    "preprocess_and_tokenize",
    "top_n",
]
