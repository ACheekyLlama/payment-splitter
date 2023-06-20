"""Module for splitting Splitwise transactions."""
import logging
from decimal import Decimal

from .client import SplitwiseClient
from .model import SwTransaction


class SplitwiseSplitter:
    """Class for splitting a Splitwise payment into its constituent expenses."""

    def __init__(self, client: SplitwiseClient) -> None:
        self._client = client

        self._logger = logging.getLogger("SplitwiseSplitter")
        self._logger.setLevel(logging.INFO)

    def get_constituent_expenses(
        self, payment: SwTransaction
    ) -> list[tuple[str, Decimal]] | None:
        """Get a list of the expenses that make up the given payment. Returns them as tuples (description, amount), or None if they could not be found."""
        constituent_transactions = self._get_constituent_transactions(payment)

        if constituent_transactions is None:
            return None

        self._remove_included_payments(constituent_transactions)

        user_id = self._client.get_user().id
        expense_tuples = [
            (txn.description, txn.get_user(user_id).get_balance())
            for txn in constituent_transactions
        ]

        return expense_tuples

    def _get_constituent_transactions(
        self, payment: SwTransaction
    ) -> list[SwTransaction] | None:
        """Get a list of all the transactions that made up this payment, or None if they could not be found."""
        transactions = [
            txn
            for txn in self._client.get_all_transactions()
            if txn.group_id == payment.group_id
        ]
        user_id = self._client.get_user().id

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

            transaction_balance_sum = sum(
                txn.get_user(user_id).get_balance() for txn in constituent_transactions
            )
            payment_balance = payment.get_user(user_id).get_balance()

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
        user_id = self._client.get_user().id

        included_payments = (txn for txn in transactions if txn.payment)
        for included_payment in included_payments:
            net_balance = included_payment.get_user(user_id).get_balance()

            # search for the expense that cancels this payment out
            matching_expenses = (
                txn
                for txn in transactions
                if (txn.date < included_payment.date)
                and (
                    txn.get_user(user_id).get_balance() + net_balance == Decimal("0.00")
                )
            )

            try:
                [matching_expense] = matching_expenses
            except ValueError as e:
                self._logger.info(str(included_payment))
                raise Exception("Could not find a matching expense for this payment.")

            self._logger.info("Found a matching payment and expense, removing them.")
            self._remove_transaction(transactions, matching_expense.id)
            self._remove_transaction(transactions, included_payment.id)

    def _remove_transaction(
        self, transactions: list[SwTransaction], transaction_id: int
    ) -> None:
        """Remove the transaction with the given id from the transactions list."""
        transaction_index = next(
            x[0] for x in enumerate(transactions) if x[1].id == transaction_id
        )
        transactions.pop(transaction_index)
