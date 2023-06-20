"""Main entrypoint module."""
import logging

from .pocketsmith.service import PocketsmithService
from .splitwise.service import SplitwiseService


def main(
    user_name: str,
    pocketsmith_key: str,
    splitwise_key: str,
    splitwise_groups: list,
    dry_run: bool = False,
):
    """Run the payment splitter."""
    logging.basicConfig()
    logger = logging.getLogger("Main")
    logger.setLevel(logging.INFO)

    pocketsmith = PocketsmithService.factory(pocketsmith_key)
    splitwise = SplitwiseService.factory(splitwise_key, splitwise_groups)

    ps_settle_up_transactions = pocketsmith.get_settle_up_transactions()
    sw_transactions = splitwise.get_all_transactions()

    if ps_settle_up_transactions:
        logger.info(
            f"Found {len(ps_settle_up_transactions)} settle-up transactions for user {user_name}."
        )

    for settle_up_transaction in ps_settle_up_transactions:
        logger.info(f"Processing transaction: {settle_up_transaction}")

        sw_payment = splitwise.get_matching_payment(
            sw_transactions,
            settle_up_transaction.get_amount(),
            settle_up_transaction.get_date(),
        )

        if sw_payment is None:
            logger.warn(f"No matching splitwise payment found, skipping.")
            continue

        logger.info(f"Found matching splitwise payment: {sw_payment}")

        constituent_expenses = splitwise.get_constituent_expenses(
            sw_transactions, sw_payment
        )

        if constituent_expenses is None:
            logger.warn(
                f"Could not split payment into its constituent expenses, skipping."
            )
            continue

        logger.info(f"Found constituent expenses: {constituent_expenses}")

        if not dry_run:
            pocketsmith.save_split_transactions(
                settle_up_transaction, constituent_expenses
            )
