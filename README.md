# Pocketsmith Payment Splitter

Pocketsmith is a useful tool for categorising your transactions and budgeting. However when it is used in conjunction with Splitwise, an app for handling shared expenses, payments between people can incorporate multiple different expenses, which affects the accuracy of your Pocketsmith budgeting.

This project is a simple integration between Pocketsmith and Splitwise, which splits the settling-up payments on Pocketsmith into the constituent payments from Splitwise. These can then be categorised as per normal.

## How it works

The program will poll the provided Pocketsmith accounts, looking for transactions with the "Splitwise" label.
When one is found, it will retrieve the list of expenses that made up that payment from Splitwise, and split the Pocketsmith transaction into those constituent transactions.

## Assumptions/Requirements

- Must be a Splitwise group of two people.
- Payments must be made in one of the following ways:
  - Settle-up payments, where the full balance is paid. These will be split by the program.
  - Single repayments for single expenses. These will be ignored by the program.
