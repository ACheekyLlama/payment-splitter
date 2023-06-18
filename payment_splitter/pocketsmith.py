"""Module for interacting with the Pocketsmith API."""
import logging
from datetime import datetime, timezone
from decimal import Decimal

import requests
from dateutil.parser import isoparse
from pydantic import BaseModel

from payment_splitter.util import to_decimal


class PsTransactionAccount(BaseModel):
    id: int


class PsTransaction(BaseModel):
    id: int
    payee: str
    date: str
    amount: float
    note: str | None
    labels: list[str]
    transaction_account: PsTransactionAccount

    def get_date(self) -> datetime:
        return isoparse(self.date).replace(tzinfo=timezone.utc)

    def get_amount(self) -> Decimal:
        return to_decimal(self.amount)

    def __str__(self) -> str:
        return str(self.dict(include={"id", "payee", "date", "amount"}))


class Pocketsmith:
    """Class for interacting with the Pocketsmith API."""

    def __init__(self, key: str) -> None:
        self._key = key

        self._logger = logging.getLogger("Pocketsmith")
        self._logger.setLevel(logging.INFO)

    def get_settle_up_transactions(self) -> list[PsTransaction]:
        """Find and return the list of uncategorised settle-up transactions in Pocketsmith."""
        user_dict = self._get_current_user()
        user_id = user_dict["id"]

        transaction_dicts = self._get_transactions(
            user_id,
            {"uncategorised": 1, "search": "splitwise"},
        )
        transactions = [
            PsTransaction(**txn)
            for txn in transaction_dicts
            if "Splitwise" in txn["labels"]
        ]

        return transactions

    def split_transaction(
        self,
        original_transaction: PsTransaction,
        new_transactions: list[tuple[str, Decimal]],
    ) -> None:
        """Split up a pocketsmith transaction, according to the given new_transactions.

        original_transaction is the original transaction in pocketsmith format
        new_transactions is the list of new transactions in an intermediate format
        """
        transaction_account = original_transaction.transaction_account.id

        created_transaction_ids = []

        try:
            for new_transaction in new_transactions:
                ps_new_transaction = {
                    "payee": f"{new_transaction[0]} {original_transaction.payee}",
                    "amount": float(new_transaction[1]),
                    "date": original_transaction.date,
                    "note": "Created by payment-splitter",
                }

                response_transaction = self._create_transaction(
                    transaction_account,
                    ps_new_transaction,
                )
                created_transaction_ids.append(response_transaction["id"])

            self._delete_transaction(original_transaction.id)
            self._logger.info(f"Split transaction into its constituents.")
        except Exception:
            self._logger.error("Error occurred while creating new transactions.")
            # rollback created transactions
            for created_transaction_id in created_transaction_ids:
                self._delete_transaction(created_transaction_id)
            self._logger.info("Rolled back all changes, no transactions were created.")

    def _get_current_user(self) -> dict:
        """Get the current user from the Pocketsmith API."""
        url = "https://api.pocketsmith.com/v2/me"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    def _get_transactions(self, user_id: int, params: dict = {}) -> list[dict]:
        """Get the list of transactions for the given user from the Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/users/{user_id}/transactions"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        data = []
        while url is not None:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data.extend(response.json())

            if "link" not in response.links:
                break

            url = response.links["next"]

        return data

    def _create_transaction(
        self, transaction_account: int, transaction_dict: dict
    ) -> dict:
        """Create a transaction in the given transaction account."""
        url = f"https://api.pocketsmith.com/v2/transaction_accounts/{transaction_account}/transactions"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.post(url, headers=headers, data=transaction_dict)
        response.raise_for_status()

        return response.json()

    def _delete_transaction(self, transaction_id: int) -> None:
        """Delete the given transaction from Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/transactions/{transaction_id}"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
