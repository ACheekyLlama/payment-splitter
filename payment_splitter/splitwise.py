import json
import math
from datetime import datetime, timedelta

import requests


class Splitwise:
    def __init__(self, key: str) -> None:
        self._key = key

    def find_settle_up_transaction(self, amount: float, timestamp: datetime):
        # get the current user
        user = self._request("https://secure.splitwise.com/api/v3.0/get_current_user")
        user_id = user["id"]

        transactions = []
        offset = 0
        while True:
            transaction_response = self._request(
                "https://secure.splitwise.com/api/v3.0/get_expenses",
                {"offset": offset},
            )

            if not transaction_response["expenses"]:
                break
            offset += len(transaction_response["expenses"])
            transactions.extend(transaction_response["expenses"])

        payments = [x for x in transactions if x["payment"]]

        matching_index = self._find_matching_payment(payments, amount, timestamp)
        matching_payment = payments[matching_index]
        preceding_payment = payments[matching_index + 1]

        constituent_transactions = [
            x
            for x in transactions
            if preceding_payment["date"] < x["date"] < matching_payment["date"]
        ]

        transaction_sum = sum(
            self._get_user(x["users"], user_id)["net_balance"]
            for x in constituent_transactions
        )
        if not math.isclose(transaction_sum + amount, 0.0):
            print(transaction_sum, amount)
            raise Exception("Transaction totals don't match.")

        # return those transactions as a list of amounts (positive or negative), and descriptions

    def _request(self, url: str, params: dict = {}) -> dict:
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}
        response = requests.get(url, headers=headers, params=params)

        return response.json()

    def _find_matching_payment(
        self, payments: list, amount: float, timestamp: datetime
    ) -> int:
        """Returns the index of the payment that matches the given amount and timestamp."""
        matching_indices = [
            x[0]
            for x in enumerate(payments)
            if self._is_matching(x[1], amount, timestamp)
        ]

        if len(matching_indices) == 0:
            print(amount)
            print(timestamp)
            raise Exception("No matching payments found.")

        if len(matching_indices) > 1:
            print(amount)
            print(timestamp)
            print(matching_indices)
            raise Exception("Multiple matching payments found.")

        return matching_indices[0]

    def _is_matching(payment: dict, amount: float, timestamp: datetime) -> bool:
        created_time = datetime.fromisoformat(payment["date"])
        time_difference = created_time - timestamp
        return math.isclose(payment["cost"], amount, abs_tol=0.01) and (
            timedelta(minutes=-30) < time_difference < timedelta(minutes=30)
        )

    def _get_user(users: list, user_id: int) -> dict:
        matching_users = [user for user in users if user["user_id"]]
        # TODO: throw exception if multiple matches found
        return matching_users[0]
