"""Module for interacting with the Splitwise API."""
import logging
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
    group_id: int | None
    description: str
    payment: bool
    cost: str
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

    def __str__(self) -> str:
        return str(self.dict(include={"id", "description", "date", "cost"}))


class Splitwise:
    """Class for interacting with the Splitwise API."""

    def __init__(self, key: str, groups: list = []) -> None:
        self._key = key
        self._groups = groups
        self._transactions: list[SwTransaction] | None = None
        user = self._request("https://secure.splitwise.com/api/v3.0/get_current_user")
        self._user_id = user["user"]["id"]

        self._logger = logging.getLogger("Splitwise")
        self._logger.setLevel(logging.INFO)

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

        constituent_transactions = self._get_constituent_transactions(
            transactions, payment
        )

        self._remove_included_payments(constituent_transactions)

        expense_tuples = [
            (txn.description, txn.get_user(self._user_id).get_balance())
            for txn in constituent_transactions
        ]

        return expense_tuples

    def _get_constituent_transactions(
        self, transactions: list[SwTransaction], payment: SwTransaction
    ) -> list[SwTransaction] | None:
        """Get a list of all the transactions that made up this payment, or None if they could not be found."""
        preceding_payments = sorted(
            (txn for txn in transactions if txn.payment and (txn.date < payment.date)),
            key=lambda x: x.date,
            reverse=True,
        )

        for preceding_payment in preceding_payments:
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
                return constituent_transactions

            self._logger.info(
                f"Transaction totals don't match, trying next payment: {transaction_balance_sum}, {payment_balance}"
            )

        return None

    def _remove_included_payments(self, transactions: list[SwTransaction]) -> None:
        """Remove any payments that were one-off payments for a single expense.

        Search for payments in the given list of transactions, find the corresponding expense, and remove both from the list.
        """
        included_payments = (txn for txn in transactions if txn.payment)
        for included_payment in included_payments:
            net_balance = included_payment.get_user(self._user_id).get_balance()

            # search for the expense that cancels this payment out
            matching_expenses = (
                txn
                for txn in transactions
                if (txn.date < included_payment.date)
                and (
                    txn.get_user(self._user_id).get_balance() + net_balance
                    == Decimal("0.00")
                )
            )
            [matching_expense] = matching_expenses

            self._logger.info("Found a matching payment and expense, removing them.")
            self._remove_transaction(transactions, matching_expense.id)
            self._remove_transaction(transactions, included_payment.id)

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

        transactions = [SwTransaction(**txn) for txn in transactions_dicts]
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
