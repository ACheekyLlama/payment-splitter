from datetime import datetime

import requests

from .pocketsmith import Pocketsmith
from .splitwise import Splitwise


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
    print(ps_settle_up_transactions)

    # find corresponding splitwise payment records
    for settle_up_transaction in ps_settle_up_transactions:
        sw_settle_up_transaction = splitwise.find_settle_up_transaction(
            settle_up_transaction["amount"],
            datetime.fromisoformat(settle_up_transaction["created_at"]),
        )

    # get all transactions included in that payment
    # split the original pocketsmith transaction into those corresponding transactions
    pass


if __name__ == "__main__":
    main()
