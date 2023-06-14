from datetime import timezone

from dateutil.parser import isoparse

from .pocketsmith import Pocketsmith
from .splitwise import Splitwise
from .util import to_decimal


def main():
    # TODO: use oauth
    with open("pocketsmith_key.txt", "r") as pocketsmith_key_file:
        pocketsmith_key = pocketsmith_key_file.read()
    with open("splitwise_key.txt", "r") as splitwise_key_file:
        splitwise_key = splitwise_key_file.read()

    pocketsmith = Pocketsmith(pocketsmith_key)
    splitwise = Splitwise(splitwise_key)

    # get all pocketsmith transactions with splitwise label
    ps_settle_up_transactions = pocketsmith.get_settle_up_transactions()

    # find corresponding splitwise payment records
    for settle_up_transaction in ps_settle_up_transactions:
        sw_payment = splitwise.get_matching_payment(
            to_decimal(settle_up_transaction["amount"]),
            isoparse(settle_up_transaction["date"]).replace(tzinfo=timezone.utc),
        )
        print(settle_up_transaction)
        print(sw_payment)

        constituent_expenses = splitwise.get_constituent_expenses(sw_payment)

        # make type definitions using typeddict
        # could also put some helper methods onto the types for e.g. getting the user balance?

        pocketsmith.split_transaction(settle_up_transaction, constituent_expenses)


if __name__ == "__main__":
    main()
