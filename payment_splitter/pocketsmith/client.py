"""Module for interacting with the Pocketsmith API."""
import requests


class PocketsmithClient:
    """Client for interacting with the Pocketsmith API."""

    def __init__(self, key: str) -> None:
        self._key = key

    def get_user_id(self) -> int:
        """Get the current user from the Pocketsmith API."""
        url = "https://api.pocketsmith.com/v2/me"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        user = response.json()

        return user["id"]

    def get_transactions(self, user_id: int, params: dict = {}) -> list[dict]:
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

    def create_transaction(
        self, transaction_account: int, transaction_dict: dict
    ) -> dict:
        """Create a transaction in the given transaction account."""
        url = f"https://api.pocketsmith.com/v2/transaction_accounts/{transaction_account}/transactions"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        response = requests.post(url, headers=headers, data=transaction_dict)
        response.raise_for_status()

        return response.json()

    def delete_transaction(self, transaction_id: int) -> None:
        """Delete the given transaction from Pocketsmith API."""
        url = f"https://api.pocketsmith.com/v2/transactions/{transaction_id}"
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}

        response = requests.delete(url, headers=headers)
        response.raise_for_status()
