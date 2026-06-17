# Language Analyzer

## High-Level Overview
Language Analyzer is a Python-based data analysis tool created for the Data in Python course Final Assignment. It processes, tokenizes, and statistically evaluates classic literary works against a baseline language dictionary. The tool helps in understanding an author's stylistic choices, vocabulary usage, and computes stylistic similarity between different texts.

---

## Installation & Usage

### Prerequisites
- **Python** (version compatible with standard data libraries like pandas)

### 1. Environment Setup
You can install this code as a package using `pip`:
```bash
# Navigate to the package directory
cd path_to_package_directory

# Install the package
pip install .
```
*(Note: If you use `uv`, you can also use `uv sync` to install dependencies).*

### 2. Running the CLI
The library provides a globally available command-line tool named `language-analyzer`. Results are written directly to the file specified by the `--output` argument.

---

#### Examples

##### Example 1: Basic Usage
The most basic usage requiring only the mandatory arguments and analyzing a single literary work:

```bash
language-analyzer \
    --dictionary data/dictionaries/polski.txt \
    --works "data/works/Mickiewicz/Pan Tadeusz.txt" \
    --output output.txt
```

##### Example 2: Minimal Usage with Multiple Works
Analyzing two literary works to compare them, using only the mandatory arguments:

```bash
language-analyzer \
    --dictionary data/dictionaries/polski.txt \
    --works "data/works/Mickiewicz/Pan Tadeusz.txt,data/works/Mickiewicz/Grażyna.txt" \
    --output output.txt
```

##### Example 3: Comprehensive Usage
Using all available arguments to process three works, extract comprehensive dictionary and file statistics, list words not found in the dictionary, calculate stylistic similarity based on the top 100 most frequent words, and apply character replacements (e.g., replacing "é" with "e"):

```bash
language-analyzer \
    --dictionary data/dictionaries/polski.txt \
    --works "data/works/Mickiewicz/Pan Tadeusz.txt, data/works/Mickiewicz/Konrad Wallenrod.txt, data/works/Mickiewicz/Grażyna.txt" \
    --dictionary-stats \
    --no-words \
    --frequencies 100 \
    --replace "é:e" \
    --output output.txt
```

---

#### Available Parameters

| Flag | Description |
|---|---|
| `--dictionary` | **(Required)** Path to the dictionary text file containing all forms of words. |
| `--works` | **(Required)** Comma-separated list of paths to literary works text files. |
| `--output` | **(Required)** Output file path where the text report results will be written. |
| `--dictionary-stats` | Output statistical data about the dictionary and the works (e.g., number of lines, words, unique words, top 10 words, letter counters). |
| `--no-words` | Analyse and list words from the Master files that do not exist in the dictionary, along with their occurrences. |
| `--frequencies N` | Calculate the `N` most frequent words and compute a similarity score (0..100) comparing the style of the works. |
| `--replace` | Optional string replacements applied before tokenizing (e.g. `--replace "é:e"`). |
