"""Module for interacting with the Splitwise API."""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from .client import SplitwiseClient
from .model import SwTransaction
from .retriever import SwTransactionRetriever
from .splitter import SwTransactionSplitter


class SplitwiseService:
    """Class for interacting with the Splitwise API."""

    def __init__(
        self, retriever: SwTransactionRetriever, splitter: SwTransactionSplitter
    ) -> None:
        self._retriever = retriever
        self._splitter = splitter

        self._logger = logging.getLogger("Splitwise")
        self._logger.setLevel(logging.INFO)

    @classmethod
    def factory(cls, key: str, groups: list[int] = []) -> SplitwiseService:
        """Factory method to create the Splitwise service."""
        client = SplitwiseClient(key)
        retriever = SwTransactionRetriever(client, groups)
        splitter = SwTransactionSplitter(client)
        return cls(retriever, splitter)

    def get_all_transactions(self) -> list[SwTransaction]:
        """Fetch and return all transactions from the Splitwise API, with caching."""
        return self._retriever.get_all_transactions()

    def get_matching_payment(
        self, transactions: list[SwTransaction], amount: Decimal, timestamp: datetime
    ) -> SwTransaction | None:
        """Get the Splitwise payment that matches the given amount and timestamp."""
        return self._retriever.get_matching_payment(transactions, amount, timestamp)

    def get_constituent_expenses(
        self, transactions: list[SwTransaction], payment: SwTransaction
    ) -> list[tuple[str, Decimal]] | None:
        """Get a list of the expenses that make up the given payment. Returns them as tuples (description, amount), or None if they could not be found."""
        return self._splitter.get_constituent_expenses(transactions, payment)
