"""Module for interacting with the Splitwise API."""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from .client import SplitwiseClient
from .model import SwTransaction
from .retriever import SplitwiseRetriever
from .splitter import SplitwiseSplitter


class SplitwiseService:
    """Class for interacting with the Splitwise API."""

    def __init__(
        self, retriever: SplitwiseRetriever, splitter: SplitwiseSplitter
    ) -> None:
        self._retriever = retriever
        self._splitter = splitter

        self._logger = logging.getLogger("SplitwiseService")
        self._logger.setLevel(logging.INFO)

    @classmethod
    def factory(cls, key: str) -> SplitwiseService:
        """Factory method to create the Splitwise service."""
        client = SplitwiseClient(key)
        retriever = SplitwiseRetriever(client)
        splitter = SplitwiseSplitter(client)
        return cls(retriever, splitter)

    def get_matching_payment(
        self, amount: Decimal, timestamp: datetime, groups: list[int] = []
    ) -> SwTransaction | None:
        """Get the Splitwise payment that matches the given amount and timestamp."""
        return self._retriever.get_matching_payment(amount, timestamp, groups)

    def get_constituent_expenses(
        self, payment: SwTransaction
    ) -> list[tuple[str, Decimal]] | None:
        """Get a list of the expenses that make up the given payment. Returns them as tuples (description, amount), or None if they could not be found."""
        return self._splitter.get_constituent_expenses(payment)
