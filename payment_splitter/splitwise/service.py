"""Module for interacting with the Splitwise API."""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from payment_splitter.splitwise.retriever import SwTransactionRetriever
from payment_splitter.splitwise.splitter import SwTransactionSplitter

from .model import SwTransaction


class SplitwiseService:
    """Class for interacting with the Splitwise API."""

    def __init__(
        self, retriever: SwTransactionRetriever, splitter: SwTransactionSplitter
    ) -> None:
        self._retriever = retriever
        self._splitter = splitter

        user = self._request("https://secure.splitwise.com/api/v3.0/get_current_user")
        self._user_id = user["user"]["id"]

        self._logger = logging.getLogger("Splitwise")
        self._logger.setLevel(logging.INFO)

    @classmethod
    def factory(cls, key: str) -> SplitwiseService:
        retriever = SwTransactionRetriever(key)
        splitter = SwTransactionSplitter()
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
