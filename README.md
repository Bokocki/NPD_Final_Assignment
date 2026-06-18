# Language Analyzer

## Overview
Language Analyzer is a Python tool built for the Data in Python course Final Assignment. It compares classic literature against a language dictionary. The tool helps users analyze an author's vocabulary, see their stylistic choices, and compare how similar different texts are to each other.

## Installation & Usage

### 1. Installation
You can easily install this code as a package using `pip`:
```bash
# Go to the package folder
cd path_to_package_directory

# Install the package
pip install .
```
*(Tip: If you use `uv`, you can run `uv sync` to install dependencies instead).*

### 2. Running the Tool
Once installed, you can run the tool from your terminal using the `language-analyzer` command. All analysis results are saved directly to the file you specify with the `--output` option.

## How It Works

To make sure the analysis is accurate and consistent, the tool follows a few simple rules:

### Dictionary Statistics
- **Character Counts**: Letters and other characters are counted directly from the raw text file. This means punctuation marks like commas are included in the "other characters" count.
- **Word Counts**: The tool reads the dictionary, changes everything to lowercase, and ignores empty lines. The first word on each line is considered a unique word (as long as it hasn't appeared first on an earlier line). The total word count includes all the comma-separated word variants on these lines.

### Dictionary Rules
- **Ignoring Punctuation**: If a word contains any punctuation (except a hyphen `-`) or spaces, the tool completely ignores it when analyzing the literary works.
- **Word Variants**: Words separated by commas are treated as different forms of the first word on that line.

### Analyzing Literary Works
- **Cleaning the Text**: Words inside the literary works are standardized. Hyphens surrounded by letters (like `word-word`) are kept, but all other punctuation is replaced with spaces.
- **Finding the Base Word**: After cleaning the text, the tool changes words to lowercase and looks them up in the dictionary to find their base form.

## Examples

### Example 1: Basic Usage
The simplest way to use the tool. This analyzes a single literary work using only the required arguments:

```bash
language-analyzer \
    --dictionary data/dictionaries/polski.txt \
    --works "data/works/Mickiewicz/Pan Tadeusz.txt" \
    --output output.txt
```

### Example 2: Comparing Two Works
Analyze two literary works to compare them, again using only the required arguments:

```bash
language-analyzer \
    --dictionary data/dictionaries/polski.txt \
    --works "data/works/Mickiewicz/Pan Tadeusz.txt, data/works/Mickiewicz/Grażyna.txt" \
    --output output.txt
```

### Example 3: Full Feature Usage
Process three works using all available options. This extracts full statistics, lists words missing from the dictionary, calculates how similar the works are (based on their 100 most frequent words), and replaces any "é" characters with "e":

```bash
language-analyzer \
    --dictionary data/dictionaries/polski.txt \
    --works "data/works/Mickiewicz/Pan Tadeusz.txt, data/works/Mickiewicz/Konrad Wallenrod.txt, data/works/Mickiewicz/Grażyna.txt" \
    --dictionary-stats \
    --no-words \
    --frequencies 100 \
    --replace é:e \
    --output output.txt
```

## Command Line Options

| Option | Description |
|---|---|
| `--dictionary` | **(Required)** Path to the dictionary text file containing word forms. |
| `--works` | **(Required)** A comma-separated list of text files (the literary works) to analyze. |
| `--output` | **(Required)** Path to the file where the results will be saved. |
| `--dictionary-stats [LEVEL]` | Output statistics about the dictionary and works. There are three levels: `basic` (lines, total/unique words), `words` (adds top 10 words), and `all` (adds letter and character counts). If you skip this option completely, it automatically defaults to `all`. |
| `--no-words` | List any words found in the literary works that are missing from the dictionary, along with how often they appear. |
| `--frequencies N` | Find the `N` most frequent words and calculate a similarity score (from 0 to 100) to compare the style of the works. |
| `--replace` | Optional rule to replace characters before analyzing the text. |
