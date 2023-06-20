import requests


class SplitwiseClient:
    """Class for interacting with the Splitwise API."""

    def __init__(self, key: str) -> None:
        self._key = key

        self._user_id: int | None = None

    def get_transactions(self, offset: int) -> list[dict]:
        """Get transactions from the Splitwise API starting from the given offset."""
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}

        response = requests.get(
            "https://secure.splitwise.com/api/v3.0/get_expenses",
            headers=headers,
            params={"offset": offset},
        )
        response.raise_for_status()
        response_dict = response.json()

        return response_dict["expenses"]

    def get_user_id(self) -> int:
        """Get the id of the currently authenticated user, with caching."""
        if self._user_id is not None:
            return self._user_id

        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}

        # TODO: error handling and data validation
        response = requests.get(
            "https://secure.splitwise.com/api/v3.0/get_current_user", headers=headers
        )
        response.raise_for_status()
        user = response.json()

        self._user_id = user["user"]["id"]
        return self._user_id
