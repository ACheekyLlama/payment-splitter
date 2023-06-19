import requests


class PocketsmithClient:
    """Class for interacting with the Pocketsmith API."""

    def __init__(self, key: str) -> None:
        self._key = key

    def get_user_id(self) -> int:
        """Get the id of the currently authenticated user."""
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}
        # TODO: error handling and data validation
        user = requests.get(
            "https://secure.splitwise.com/api/v3.0/get_current_user", headers=headers
        )
        return user["user"]["id"]
