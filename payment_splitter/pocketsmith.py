import requests


class Pocketsmith:
    def __init__(self, key: str) -> None:
        self._key = key

    def get_settle_up_transactions(self):
        user_dict = self._request("https://api.pocketsmith.com/v2/me")
        user_id = user_dict["id"]

        splitwise_transactions = self._request_paginated(
            f"https://api.pocketsmith.com/v2/users/{user_id}/transactions",
            {"uncategorised": 1, "search": "splitwise"},
        )

        return splitwise_transactions

    def split_transaction(self) -> None:
        pass

    def _request(self, url: str, params: dict = {}) -> dict:
        headers = {"X-Developer-Key": self._key, "accept": "application/json"}
        response = requests.get(url, headers=headers, params=params)

        return response.json()

    def _request_paginated(self, url: str, params: dict = {}) -> list[dict]:
        data = []

        while url is not None:
            headers = {"X-Developer-Key": self._key, "accept": "application/json"}
            response = requests.get(url, headers=headers, params=params)
            data.extend(response.json())

            url = response.links.get("next")

        return data
