"""Dataset adapters → uniform eval-item schema.

Each adapter: load(path_or_id, n=None) -> iterator of:
  {"id": str, "context": str, "question": str, "answer": str,
   "type": str, "meta": dict}
"""
from .coqa import load as coqa
from .squad import load as squad
from .refactoring import load as refactoring
