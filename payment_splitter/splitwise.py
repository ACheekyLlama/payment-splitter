from datetime import datetime, timedelta
from decimal import Decimal
from typing import TypedDict

import requests
from dateutil.parser import isoparse

from .util import to_decimal


class SwTransaction(TypedDict):
    group_id: int
    payment: bool


class Splitwise:
    def __init__(self, key: str) -> None:
        self._key = key
        self._transactions = None

    def get_matching_payment(self, amount: Decimal, timestamp: datetime) -> dict:
        """Get the splitwise payment that matches the given amount and timestamp."""
        transactions = self._fetch_transactions()

        matching_payments = [
            x
            for x in transactions
            if x["payment"] and self._is_matching(x, amount, timestamp)
        ]

        if len(matching_payments) == 0:
            print(amount)
            print(timestamp)
            raise Exception("No matching payments found.")

        if len(matching_payments) > 1:
            print(amount)
            print(timestamp)
            print(matching_payments)
            raise Exception("Multiple matching payments found.")

        [payment] = matching_payments

        return payment

    def get_constituent_expenses(self, payment: dict) -> list[tuple[str, Decimal]]:
        """Get a list of the expenses that make up the given payment. Returns them as tuples (description, amount)."""
        user = self._request("https://secure.splitwise.com/api/v3.0/get_current_user")
        user_id = user["user"]["id"]

        transactions = [
            x
            for x in self._fetch_transactions()
            if x["group_id"] == payment["group_id"]
        ]

        preceding_payments = (
            x for x in transactions if x["payment"] and (x["date"] < payment["date"])
        )

        constituent_transactions = []
        while True:
            preceding_payment = next(preceding_payments)

            constituent_transactions = [
                x
                for x in transactions
                if preceding_payment["date"] < x["date"] < payment["date"]
            ]

            transaction_balances = (
                self._get_user_balance(x, user_id) for x in constituent_transactions
            )
            transaction_balance_sum = sum(transaction_balances)
            payment_balance = self._get_user_balance(payment, user_id)

            if transaction_balance_sum + payment_balance == Decimal("0.00"):
                print("Transaction totals match.")
                break

            print(
                f"Transaction totals don't match, trying next payment: {transaction_balance_sum}, {payment_balance}"
            )

        included_payments = (x for x in constituent_transactions if x["payment"])
        for included_payment in included_payments:
            net_balance = self._get_user_balance(included_payment, user_id)

            # search for the expense that cancels this payment out
            matching_expenses = (
                x
                for x in constituent_transactions
                if (x["date"] < included_payment["date"])
                and (
                    self._get_user_balance(x, user_id) + net_balance == Decimal("0.00")
                )
            )
            [matching_expense] = matching_expenses

            print("Found a matching payment and expense, removing them.")

            # remove the payment and expense
            self._remove_transaction(constituent_transactions, matching_expense["id"])
            self._remove_transaction(constituent_transactions, included_payment["id"])

        output = [
            (x["description"], self._get_user_balance(x, user_id))
            for x in constituent_transactions
        ]

        # return those transactions as a list of amounts (positive or negative), and descriptions
        print(output)

        return output

    def _request(self, url: str, params: dict = {}) -> dict:
        """Make a get request to the Splitwise API."""
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}
        response = requests.get(url, headers=headers, params=params)

        return response.json()

    def _fetch_transactions(self) -> list:
        """Fetch and return all transactions from the Splitwise API, with caching."""
        if self._transactions is not None:
            return self._transactions

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

        self._transactions = transactions
        return transactions

    def _is_matching(self, payment: dict, amount: Decimal, timestamp: datetime) -> bool:
        """Check if the given payment matches the given amount and timestamp."""
        payment_date = isoparse(payment["date"])
        time_difference = payment_date - timestamp
        return (to_decimal(payment["cost"]) == amount) and (
            timedelta(days=-2) < time_difference < timedelta(days=2)
        )

    def _get_user_balance(self, transaction: dict, user_id: int) -> Decimal:
        """Get the net balance change for the given user id from the given transaction."""
        matching_users = [
            user for user in transaction["users"] if user["user_id"] == user_id
        ]
        [matching_user] = matching_users
        return to_decimal(matching_user["net_balance"])

    def _remove_transaction(self, transactions: list, transaction_id: int) -> None:
        """Remove the transaction with the given id from the transactions list."""
        transaction_index = next(
            x[0] for x in enumerate(transactions) if x[1]["id"] == transaction_id
        )
        transactions.pop(transaction_index)
