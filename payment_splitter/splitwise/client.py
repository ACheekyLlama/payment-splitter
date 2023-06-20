import requests

from .model import SwTransaction, SwUser


class SplitwiseClient:
    """Class for interacting with the Splitwise API."""

    def __init__(self, key: str) -> None:
        self._key = key

        self._transactions: list[SwTransaction] | None = None
        self._user: SwUser | None = None

    def get_all_transactions(self) -> list[SwTransaction]:
        """Get all transactions from the Splitwise API, with caching."""
        if self._transactions is not None:
            return self._transactions

        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}
        url = "https://secure.splitwise.com/api/v3.0/get_expenses"

        transactions: list[SwTransaction] = []
        offset = 0
        while True:
            response = requests.get(url=url, headers=headers, params={"offset": offset})
            response.raise_for_status()

            response_transactions = [
                SwTransaction(**txn) for txn in response.json()["expenses"]
            ]

            if not response_transactions:
                break

            offset += len(response_transactions)
            transactions.extend(response_transactions)

        self._transactions = transactions

        return transactions

    def get_user(self) -> SwUser:
        """Get the currently authenticated user, with caching."""
        if self._user is not None:
            return self._user

        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}
        url = "https://secure.splitwise.com/api/v3.0/get_current_user"

        # TODO: error handling
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        response_dict = response.json()

        self._user = SwUser(**response_dict["user"])

        return self._user
