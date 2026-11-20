"""Convenience wrapper for the diagram generator.

The editable source and its output live beside the PNGs in docs/diagrams/.
"""

from pathlib import Path
import runpy

runpy.run_path(Path(__file__).resolve().parents[1] / "docs" / "diagrams" / "generate_diagrams.py", run_name="__main__")
