"""Wikidle NLP pipeline — article selection and redaction."""

from pipeline import article_store, config, filters, wikipedia_client

__all__ = ["config", "filters", "wikipedia_client", "article_store"]
