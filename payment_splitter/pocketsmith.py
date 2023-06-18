"""Module for interacting with the Pocketsmith API."""
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
    labels: list[str]
    transaction_account: PsTransactionAccount

    def get_date(self) -> datetime:
        return isoparse(self.date).replace(tzinfo=timezone.utc)

    def get_amount(self) -> Decimal:
        return to_decimal(self.amount)


class Pocketsmith:
    """Class for interacting with the Pocketsmith API."""

    def __init__(self, key: str) -> None:
        self._key = key

    def get_settle_up_transactions(self) -> list[PsTransaction]:
        """Find and return the list of uncategorised settle-up transactions in Pocketsmith."""
        user_dict = self._get_request("https://api.pocketsmith.com/v2/me")
        user_id = user_dict["id"]

        transaction_dicts = self._get_request_paginated(
            f"https://api.pocketsmith.com/v2/users/{user_id}/transactions",
            {"uncategorised": 1, "search": "splitwise"},
        )
        transactions = [
            PsTransaction(txn)
            for txn in transaction_dicts
            if "Splitwise" in txn["labels"]
        ]

        print(f"Found {len(transactions)} settle-up transactions.")

        return transactions

    def split_transaction(
        self,
        original_transaction: PsTransaction,
        new_transactions: list[tuple[str, Decimal]],
        dry_run: bool = False,
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

                print(f"Creating transaction: {ps_new_transaction}")

                if not dry_run:
                    response_transaction = self._post_request(
                        f"https://api.pocketsmith.com/v2/transaction_accounts/{transaction_account}/transactions",
                        ps_new_transaction,
                    )
                    created_transaction_ids.append(response_transaction["id"])

            if not dry_run:
                print(f"Deleting original transaction: {original_transaction}")
                self._delete_request(
                    f"https://api.pocketsmith.com/v2/transactions/{original_transaction.id}"
                )
        except Exception:
            print("Error occurred while creating new transactions.")
            # rollback created transactions
            for created_transaction_id in created_transaction_ids:
                self._delete_request(
                    f"https://api.pocketsmith.com/v2/transactions/{created_transaction_id}"
                )

    def _get_request(self, url: str, params: dict = {}) -> dict:
        """Make a get request to the Pocketsmith API."""
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.get(url, headers=headers, params=params)

        return response.json()

    def _get_request_paginated(self, url: str, params: dict = {}) -> list[dict]:
        """Make a get request to the Pocketsmith API and collect the paginated results into a list."""
        data = []

        while url is not None:
            headers = {"X-Developer-Key": self._key, "accept": "application/json"}
            response = requests.get(url, headers=headers, params=params)
            data.extend(response.json())

            if "link" not in response.links:
                break

            url = response.links["next"]

        return data

    def _post_request(self, url: str, data: dict) -> dict:
        """Make a post request to the Pocketsmith API."""
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

        return response.json()

    def _delete_request(self, url: str) -> None:
        """Make a delete request to the Pocketsmith API."""
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
