"""Module for handling Pocketsmith transactions."""
from __future__ import annotations

import logging
from decimal import Decimal

from .client import PocketsmithClient
from .model import PsTransaction
from .retriever import PocketsmithRetriever
from .saver import PocketsmithSaver


class PocketsmithService:
    """Service for handling Pocketsmith transactions."""

    def __init__(
        self,
        retriever: PocketsmithRetriever,
        saver: PocketsmithSaver,
    ) -> None:
        self._retriever = retriever
        self._saver = saver

        self._logger = logging.getLogger("PocketsmithService")
        self._logger.setLevel(logging.INFO)

    @classmethod
    def factory(cls, key: str) -> PocketsmithService:
        """Factory method for creating the Pocketsmith service."""
        client = PocketsmithClient(key)
        retriever = PocketsmithRetriever(client)
        splitter = PocketsmithSaver(client)

        return cls(retriever, splitter)

    def get_settle_up_transactions(self) -> list[PsTransaction]:
        """Find and return the list of uncategorised settle-up transactions in Pocketsmith."""
        return self._retriever.get_settle_up_transactions()

    def save_split_transactions(
        self,
        original_transaction: PsTransaction,
        new_transactions: list[tuple[str, Decimal]],
    ) -> None:
        """Split up a pocketsmith transaction, according to the given new_transactions.

        original_transaction is the original transaction in pocketsmith format
        new_transactions is the list of new transactions in an intermediate format
        """
        self._saver.save_split_transactions(original_transaction, new_transactions)
