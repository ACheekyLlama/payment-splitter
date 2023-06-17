"""Module for interacting with the Splitwise API."""
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from dateutil.parser import isoparse
from pydantic import BaseModel

from .util import to_decimal


class SwTransactionUser(BaseModel):
    """Model representing the user object inside a Splitwise transaction."""

    user_id: int
    net_balance: str

    def get_balance(self) -> Decimal:
        """Get the net balance for the user, as a Decimal."""
        return to_decimal(self.net_balance)


class SwTransaction(BaseModel):
    """Model representing a Splitwise transaction returned by the API."""

    id: int
    group_id: int
    description: str
    payment: bool
    date: str
    users: list[SwTransactionUser]

    def get_date(self) -> datetime:
        """Get the date of the transaction, as a datetime."""
        return isoparse(self.date)

    def get_user(self, user_id: int) -> SwTransactionUser:
        """Get the user object for the given id."""
        matching_users = [user for user in self.users if user.user_id == user_id]
        [matching_user] = matching_users
        return matching_user


class Splitwise:
    """Class for interacting with the Splitwise API."""

    def __init__(self, key: str, groups: list = []) -> None:
        self._key = key
        self._groups = groups
        self._transactions: list[SwTransaction] | None = None
        user = self._request("https://secure.splitwise.com/api/v3.0/get_current_user")
        self._user_id = user["user"]["id"]

    def get_matching_payment(
        self, amount: Decimal, timestamp: datetime
    ) -> SwTransaction | None:
        """Get the Splitwise payment that matches the given amount and timestamp."""
        transactions = self._fetch_transactions()

        matching_payments = [
            txn
            for txn in transactions
            if txn.payment and self._is_matching(txn, amount, timestamp)
        ]

        if not matching_payments:
            return None

        [payment] = matching_payments
        return payment

    def get_constituent_expenses(
        self, payment: SwTransaction
    ) -> list[tuple[str, Decimal]]:
        """Get a list of the expenses that make up the given payment. Returns them as tuples (description, amount)."""
        transactions = [
            txn
            for txn in self._fetch_transactions()
            if txn.group_id == payment.group_id
        ]

        preceding_payments = iter(
            sorted(
                (
                    txn
                    for txn in transactions
                    if txn.payment and (txn.date < payment.date)
                ),
                key=lambda x: x.date,
                reverse=True,
            )
        )

        constituent_transactions = []
        while True:
            try:
                preceding_payment = next(preceding_payments)
            except StopIteration:
                raise Exception(
                    "Could not find the constituent expenses. Check that you have not made any partial payments."
                )

            constituent_transactions = [
                txn
                for txn in transactions
                if preceding_payment.date < txn.date < payment.date
            ]

            transaction_balances = (
                txn.get_user(self._user_id).get_balance()
                for txn in constituent_transactions
            )
            transaction_balance_sum = sum(transaction_balances)
            payment_balance = payment.get_user(self._user_id).get_balance()

            if transaction_balance_sum + payment_balance == Decimal("0.00"):
                print("Transaction totals match.")
                break

            print(
                f"Transaction totals don't match, trying next payment: {transaction_balance_sum}, {payment_balance}"
            )

        included_payments = (txn for txn in constituent_transactions if txn.payment)
        for included_payment in included_payments:
            net_balance = included_payment.get_user(self._user_id).get_balance()

            # search for the expense that cancels this payment out
            matching_expenses = (
                txn
                for txn in constituent_transactions
                if (txn.date < included_payment.date)
                and (
                    txn.get_user(self._user_id).get_balance() + net_balance
                    == Decimal("0.00")
                )
            )
            [matching_expense] = matching_expenses

            print("Found a matching payment and expense, removing them.")

            # remove the payment and expense
            self._remove_transaction(constituent_transactions, matching_expense["id"])
            self._remove_transaction(constituent_transactions, included_payment["id"])

        output = [
            (txn["description"], txn.get_user(self._user_id).get_balance())
            for txn in constituent_transactions
        ]

        # return those transactions as a list of amounts (positive or negative), and descriptions
        print(output)

        return output

    def _request(self, url: str, params: dict = {}) -> dict:
        """Make a get request to the Splitwise API."""
        headers = {"Authorization": f"Bearer {self._key}", "accept": "application/json"}
        response = requests.get(url, headers=headers, params=params)

        return response.json()

    def _fetch_transactions(self) -> list[SwTransaction]:
        """Fetch and return all transactions from the Splitwise API, with caching."""
        if self._transactions is not None:
            return self._transactions

        transactions_dicts = []
        offset = 0
        while True:
            transaction_response = self._request(
                "https://secure.splitwise.com/api/v3.0/get_expenses",
                {"offset": offset},
            )

            if not transaction_response["expenses"]:
                break
            offset += len(transaction_response["expenses"])
            transactions_dicts.extend(transaction_response["expenses"])

        transactions = [SwTransaction(x) for x in transactions_dicts]
        if self._groups:
            transactions = [x for x in transactions if x.group_id in self._groups]

        self._transactions = transactions

        return transactions

    def _is_matching(
        self, payment: SwTransaction, amount: Decimal, timestamp: datetime
    ) -> bool:
        """Check if the given payment matches the given amount and timestamp."""
        payment_date = payment.get_date()
        time_difference = payment_date - timestamp

        is_matching_amount = (
            payment.get_user(self._user_id).get_balance() + amount
        ) == 0
        is_matching_timestamp = timedelta(days=-2) < time_difference < timedelta(days=2)

        return is_matching_amount and is_matching_timestamp

    def _remove_transaction(
        self, transactions: list[SwTransaction], transaction_id: int
    ) -> None:
        """Remove the transaction with the given id from the transactions list."""
        transaction_index = next(
            x[0] for x in enumerate(transactions) if x[1].id == transaction_id
        )
        transactions.pop(transaction_index)
