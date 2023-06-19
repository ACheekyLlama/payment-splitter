# Pocketsmith Payment Splitter

Pocketsmith is a useful tool for categorising your transactions and budgeting. However when it is used in conjunction with Splitwise, an app for handling shared expenses, payments between people can incorporate multiple different expenses, which affects the accuracy of your Pocketsmith budgeting.

This project is a simple integration between Pocketsmith and Splitwise, which splits the settling-up payments on Pocketsmith into the constituent payments from Splitwise. These can then be categorised as per normal.

## How it works

The program will poll the provided Pocketsmith accounts, looking for transactions with the "Splitwise" label.
When one is found, it will retrieve the list of expenses that made up that payment from Splitwise, and split the Pocketsmith transaction into those constituent transactions.

## Usage

- Compatible with Python >= 3.10
- Install dependencies with `pip install -r requirements.txt`
- Run with `python -m payment_splitter config.json [--dry-run]`
  - Configuration file (see `config-example.json`)
    - `name`: Display name of the user, for logging.
    - `pocketsmith_api_key`: API key for the Pocketsmith user.
    - `splitwise_api_key`: API key for the Splitwise user.
    - `splitwise_groups`: IDs of the Splitwise groups that should be searched. Leave empty to include all of the user's Splitwise transactions.
  - Other command-line arguments:
    - `--dry-run`: optional command-line argument which prevents the program from writing anything to Pocketsmith, so that the log output can be checked.

## Extra Assumptions/Requirements

- Must be a Splitwise group of two people.
- Payments must be made in one of the following ways:
  - Settle-up payments, where the full balance is paid. The program will split these in Pocketsmith.
  - Single repayments for single expenses. The program will ignore these in Pocketsmith.
