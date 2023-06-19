"""Module for saving Pocketsmith transactions."""
import logging
from decimal import Decimal

import requests

from .model import PsTransaction


class PsTransactionSaver:
    """Class for saving newly-split Pocketsmith transactions."""

    def __init__(self, key: str) -> None:
        self._key = key

        self._logger = logging.getLogger("PsTransactionSplitter")
        self._logger.setLevel(logging.INFO)

    def save_split_transactions(
        self,
        original_transaction: PsTransaction,
        new_transactions: list[tuple[str, Decimal]],
    ) -> None:
        """Save the newly created pocketsmith transactions, and delete the original.

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
