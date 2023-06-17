"""Module for interacting with the Pocketsmith API."""
from decimal import Decimal

import requests


class Pocketsmith:
    """Class for interacting with the Pocketsmith API."""

    def __init__(self, key: str) -> None:
        self._key = key

    def get_settle_up_transactions(self):
        """Find and return the list of uncategorised settle-up transactions in Pocketsmith."""
        user_dict = self._get_request("https://api.pocketsmith.com/v2/me")
        user_id = user_dict["id"]

        splitwise_transactions = self._get_request_paginated(
            f"https://api.pocketsmith.com/v2/users/{user_id}/transactions",
            {"uncategorised": 1, "search": "splitwise"},
        )

        # filter down to only those with the label

        print(f"Found {len(splitwise_transactions)} settle-up transactions.")

        return splitwise_transactions

    def split_transaction(
        self, original_transaction: dict, new_transactions: list[tuple[str, Decimal]]
    ) -> None:
        """Split up a pocketsmith transaction, according to the given new_transactions.

        original_transaction is the original transaction in pocketsmith format
        new_transactions is the list of new transactions in an intermediate format
        """
        transaction_account = original_transaction["transaction_account"]["id"]

        created_transaction_ids = []

        try:
            for new_transaction in new_transactions:
                ps_new_transaction = {
                    "payee": f"{new_transaction[0]} {original_transaction['payee']}",
                    "amount": float(new_transaction[1]),
                    "date": original_transaction["date"],
                    "note": "Created by payment-splitter",
                }

                print(f"Creating transaction: {ps_new_transaction}")
                response_transaction = self._post_request(
                    f"https://api.pocketsmith.com/v2/transaction_accounts/{transaction_account}/transactions",
                    ps_new_transaction,
                )
                created_transaction_ids.append(response_transaction["id"])

            print(f"Deleting original transaction: {original_transaction}")
            self._delete_request(
                f"https://api.pocketsmith.com/v2/transactions/{original_transaction['id']}"
            )
        except Exception as e:
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
