"""Persistence layer (WBS-B1).

`base` holds the declarative Base, shared mixins and Charter-frozen enums.
`models` holds every ORM entity built in B1 (K01–K06 + §2.9 raw-data tables
+ model_version). Other layers import from `knowledge.db.models`.
"""

from knowledge.db.base import Base

__all__ = ["Base"]
