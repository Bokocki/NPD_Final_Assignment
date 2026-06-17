"""Profile the language-analyzer CLI and generate performance visualizations."""

import cProfile
import pstats
import subprocess
import sys
from pathlib import Path

from language_analyzer.cli import main


def run() -> None:
    """Run the profiler with default arguments and generate reports."""
    results_dir = Path("profiling")
    results_dir.mkdir(parents=True, exist_ok=True)

    sys.argv = [
        "language_analyzer",
        "--dictionary",
        "data/dictionaries/polski.txt",
        "--works",
        "data/works/Mickiewicz/Pan Tadeusz.txt, \
            data/works/Mickiewicz/Konrad Wallenrod.txt, \
                data/works/Mickiewicz/Grażyna.txt",
        "--dictionary-stats",
        "--no-words",
        "--frequencies",
        "100",
        "--replace",
        "é:e",
        "--output",
        "output.txt",
    ]

    profiler = cProfile.Profile()
    profiler.enable()
    try:
        main()
    except SystemExit:
        pass
    profiler.disable()

    prof_path = results_dir / "profile.prof"
    profiler.dump_stats(str(prof_path))

    # Profiling results saved to a text file
    txt_path = results_dir / "profiling_results.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        pstats.Stats(profiler, stream=f).sort_stats("cumtime").print_stats(50)
    print(f"Profiling results saved to {txt_path}")

    # Flame graph of profiling results
    svg_flame = results_dir / "flame_graph.svg"
    try:
        with open(svg_flame, "w", encoding="utf-8") as out:
            subprocess.run(
                ["uv", "run", "flameprof", str(prof_path)], stdout=out, check=True
            )
        print(f"Flame graph saved to {svg_flame}")
    except Exception as e:
        print(f"Flame graph failed: {e}")

    # Call graph of profiling results
    svg_call = results_dir / "call_graph.svg"
    try:
        gprof = subprocess.run(
            ["uv", "run", "gprof2dot", "-f", "pstats", str(prof_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            ["dot", "-Tsvg", "-o", str(svg_call)],
            input=gprof.stdout,
            text=True,
            check=True,
        )
        print(f"Call graph saved to {svg_call}")
    except Exception as e:
        print(f"Call graph failed: {e}")


if __name__ == "__main__":
    run()
