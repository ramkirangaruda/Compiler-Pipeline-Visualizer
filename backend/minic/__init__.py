"""MiniC: a small statically-typed, C-like language and its compiler pipeline."""
from .pipeline import compile_source, run_frontend

__all__ = ["compile_source", "run_frontend"]
