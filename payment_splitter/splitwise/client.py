import requests

from .model import SwTransaction, SwUser


class SplitwiseClient:
    """Class for interacting with the Splitwise API."""

    def __init__(self, key: str) -> None:
        self._key = key

        self._user: SwUser | None = None

    def get_transactions(self, offset: int) -> list[SwTransaction]:
        """Get transactions from the Splitwise API starting from the given offset."""
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}

        response = requests.get(
            "https://secure.splitwise.com/api/v3.0/get_expenses",
            headers=headers,
            params={"offset": offset},
        )
        response.raise_for_status()
        response_dict = response.json()

        transactions = [SwTransaction(**txn) for txn in response_dict["expenses"]]

        return transactions

    def get_user(self) -> SwUser:
        """Get the currently authenticated user, with caching."""
        if self._user is not None:
            return self._user

        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}

        # TODO: error handling and data validation
        response = requests.get(
            "https://secure.splitwise.com/api/v3.0/get_current_user", headers=headers
        )
        response.raise_for_status()
        response_dict = response.json()

        self._user = SwUser(**response_dict["user"])

        return self._user
