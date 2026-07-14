"""Shared base class for all Picnic data models."""

from pydantic import BaseModel, ConfigDict, Field, SkipValidation


class PicnicModel(BaseModel):
    """Base for every Picnic model.

    Design goals, given that the Picnic API varies by country and A/B test:

    - ``extra="ignore"`` so unknown/new fields never break parsing.
    - ``populate_by_name=True`` so fields can carry a ``Field(alias=...)`` for
      Picnic's raw keys while staying accessible by their pythonic name.
    - Every top-level model keeps the original payload in :attr:`raw` (excluded
      from ``model_dump()``) so callers can always reach data we haven't modelled
      yet. It is stored verbatim (no copy/validation) so it stays the exact
      object returned by the API, and is excluded from ``model_dump()``.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    raw: SkipValidation[dict | None] = Field(default=None, exclude=True, repr=False)


__all__ = ["PicnicModel"]
