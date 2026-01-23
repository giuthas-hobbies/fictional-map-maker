"""
Fimama doc generator.
"""
from pathlib import Path

import pdoc


def main():
    """
    Generate the docs for fimama.

    Run with `uv run pre-deployment/generate_api_docs.py` at project root.
    """
    source_path = Path("src/fimama/")
    pdoc.render.configure(docformat="numpy", )
    pdoc.pdoc(source_path, output_directory=Path("docs/api"))


if __name__ == "__main__":
    main()
