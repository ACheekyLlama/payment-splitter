"""Module for interacting with the Pocketsmith API."""
import logging

import requests

from .model import PsTransaction, PsUser


class PocketsmithClient:
    """Client for interacting with the Pocketsmith API."""

    def __init__(self, key: str) -> None:
        self._key = key

        self._logger = logging.getLogger("PocketsmithClient")
        self._logger.setLevel(logging.INFO)

    def get_user(self) -> PsUser:
        """Get the current user from the Pocketsmith API."""
        url = "https://api.pocketsmith.com/v2/me"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user_dict = response.json()

        user = PsUser(**user_dict)

        return user

    def get_transactions(self, user_id: int, params: dict = {}) -> list[PsTransaction]:
        """Get the list of transactions for the given user from the Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/users/{user_id}/transactions"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        transaction_dicts: list[dict] = []
        while url is not None:
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
            except requests.exceptions.ConnectionError:
                self._logger.error(
                    "Connection error while reading transactions from Pocketsmith."
                )
                return []

            transaction_dicts.extend(response.json())

            if "link" not in response.links:
                break

            url = response.links["next"]

        transactions = [PsTransaction(**txn) for txn in transaction_dicts]

        return transactions

    def create_transaction(
        self, transaction_account: int, transaction_dict: dict
    ) -> PsTransaction:
        """Create a transaction in the given transaction account using the Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/transaction_accounts/{transaction_account}/transactions"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        try:
            response = requests.post(url, headers=headers, data=transaction_dict)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            self._logger.error(
                "Connection error occurred while creating Pocketsmith transactions."
            )
            raise

        response_dict = response.json()

        return PsTransaction(**response_dict)

    def delete_transaction(self, transaction_id: int) -> None:
        """Delete the given transaction from the Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/transactions/{transaction_id}"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            self._logger.error(
                "Connection error occurred while deleting Pocketsmith transactions."
            )
            raise
