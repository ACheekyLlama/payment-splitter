"""Main entrypoint module."""
from datetime import timezone

from dateutil.parser import isoparse

from .pocketsmith import Pocketsmith
from .splitwise import Splitwise
from .util import to_decimal


def main(
    pocketsmith_key: str,
    splitwise_key: str,
    splitwise_groups: list,
    dry_run: bool = False,
):
    """Run the payment splitter."""
    pocketsmith = Pocketsmith(pocketsmith_key)
    splitwise = Splitwise(splitwise_key, splitwise_groups)

    ps_settle_up_transactions = pocketsmith.get_settle_up_transactions()

    for settle_up_transaction in ps_settle_up_transactions:
        print(
            f"Processing transaction: id: {settle_up_transaction['id']}, amount: {settle_up_transaction['amount']}"
        )
        sw_payment = splitwise.get_matching_payment(
            to_decimal(settle_up_transaction["amount"]),
            isoparse(settle_up_transaction["date"]).replace(tzinfo=timezone.utc),
        )

        if sw_payment is None:
            print(f"No matching splitwise payment found, skipping.")
            continue

        print(f"Found matching splitwise payment: {sw_payment['id']}")

        # log these as debug?
        # print(settle_up_transaction)
        # print(sw_payment)

        constituent_expenses = splitwise.get_constituent_expenses(sw_payment)

        # make type definitions using typeddict
        # could also put some helper methods onto the types for e.g. getting the user balance?

        pocketsmith.split_transaction(
            settle_up_transaction, constituent_expenses, dry_run=dry_run
        )
