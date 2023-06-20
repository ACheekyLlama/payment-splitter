"""Module for saving Pocketsmith transactions."""
import logging
from decimal import Decimal

from .client import PocketsmithClient
from .model import PsTransaction


class PocketsmithSaver:
    """Class for saving newly-split transactions to Pocketsmith."""

    def __init__(self, client: PocketsmithClient) -> None:
        self._client = client

        self._logger = logging.getLogger("PocketsmithSaver")
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

                response_transaction = self._client.create_transaction(
                    transaction_account,
                    ps_new_transaction,
                )
                created_transaction_ids.append(response_transaction.id)

            self._client.delete_transaction(original_transaction.id)
            self._logger.info(f"Split transaction into its constituents.")
        except Exception:
            self._logger.error("Error occurred while creating new transactions.")
            # rollback created transactions
            for created_transaction_id in created_transaction_ids:
                self._client.delete_transaction(created_transaction_id)
            self._logger.info("Rolled back all changes, no transactions were created.")
