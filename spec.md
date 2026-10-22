PYTHON CODING ASSESSMENT: SETTLE SHARED EXPENSES FROM CSV

OBJECTIVE



Implement a Python program that reads shared expenses from a CSV file, calculates each person's net balance, and generates payments that settle all debts.



The program must minimise the number of payments required to settle each test case globally.



INPUT FILE



The program must accept a CSV file named inputs.csv.



The CSV must contain these columns:



case\_id: Identifies an independent test case.

payer: Name of the person who paid the expense.

amount: Expense amount in integer cents.

participants: Semicolon-separated list of people sharing the expense.



Example:



case\_id,payer,amount,participants 1,Alice,1000,Alice;Bob 1,Bob,500,Alice;Bob 2,Charlie,900,Charlie;Dave;Eve



Rows with the same case\_id belong to the same scenario. Each distinct case\_id must be processed independently.



Use Python's standard-library csv module.



EXPENSE RULES

All monetary amounts are expressed in integer cents.

Each expense is split equally among its participants.

The payer does not have to be a participant.

Participants may appear in multiple expenses.

Different expenses may have different participant lists.

Names may contain spaces or Unicode characters.

Duplicate participants within one expense are invalid.

Zero-value expenses are allowed.

Negative amounts are invalid.



Rounding rule:



If an expense cannot be divided equally into whole cents, allocate the remaining cents one at a time to participants in the order listed in the CSV.



For example, 100 cents shared by Alice, Bob and Charlie is allocated as follows:



Alice: 34 cents

Bob: 33 cents

Charlie: 33 cents



The sum of the allocated shares must equal the original expense amount.



REQUIRED FUNCTION



Implement:



def settle\_expenses(expenses):

&#x20;   """

&#x20;   Calculate the minimum number of payments

&#x20;   required to settle a collection of expenses.



&#x20;   Args:

&#x20;       expenses: A list of expense dictionaries.



&#x20;   Returns:

&#x20;       A list of payment dictionaries.

&#x20;   """





Each expense dictionary has this structure:



{

&#x20;   "payer": "Alice",

&#x20;   "amount": 1000,

&#x20;   "participants": \["Alice", "Bob"]

}





Each payment dictionary must have this structure:



{

&#x20;   "from": "Bob",

&#x20;   "to": "Alice",

&#x20;   "amount": 500

}





Payment amounts must be positive integers representing cents.



BALANCE CALCULATION



For every person, calculate:



net balance = total amount paid - total amount owed





Interpret balances as follows:



Positive balance: the person is owed money.

Negative balance: the person owes money.

Zero balance: the person has nothing to pay or receive.



Only non-zero balances need to be considered during settlement.



SETTLEMENT REQUIREMENTS



For each case\_id independently:



Calculate each person's net balance.

Generate payments from debtors to creditors.

Ensure every person's final balance is zero.

Never generate zero-value or negative-value payments.

Never generate a payment from a person to themselves.

Minimise the number of payments globally.

Use no more than n - 1 payments for n non-zero balances.

Never transfer more than a debtor owes or a creditor is owed.

Ensure all outstanding debts are settled exactly.



A greedy algorithm that produces valid payments but does not guarantee the globally minimum number of payments does not satisfy the optimisation requirement.



CSV LOADING AND PROCESSING



The program must:



Accept the input CSV filename as a command-line argument.

Read the file using UTF-8 encoding.

Validate the required column names.

Parse amount as an integer.

Split participants on semicolons and trim whitespace.

Group expenses by case\_id.

Process each case independently.

Display settlement results for every case.

Report invalid input clearly, including the CSV row number where possible.



Use only the Python standard library. No database, web service or third-party package is required.



INPUT VALIDATION



Reject invalid input, including:



Missing or unreadable input files.

Missing required CSV columns.

Missing case\_id or payer values.

Empty payer or participant names.

Empty participant lists.

Duplicate participants within one expense.

Negative amounts.

Non-integer amounts.

Boolean values used as monetary amounts.

Malformed CSV rows.



Zero-value expenses are valid and must produce no payment when no balances remain outstanding.



OUTPUT FORMAT



For each case, display its ID and the payments needed to settle its expenses.



Example:



Case 1: Bob -> Alice: 250 cents



Case 2: No payments required.



Payment ordering is not significant. Multiple payment lists are acceptable if they settle all balances using the globally minimum number of transfers.



DELIVERABLES



Submit the following files:



settle\_expenses.py Contains the settlement algorithm.

run\_csv\_tests.py Loads the CSV file and executes each test case.

edge\_case\_inputs.csv Contains the supplied test dataset.

Automated unit tests.



Also provide:



A brief explanation of the algorithm.

Time and space complexity analysis.

Documentation of assumptions and limitations.

TESTING REQUIREMENTS



Test the implementation against:



Empty input and zero-value expenses.

One participant and two participants.

Even and uneven expense splits.

A payer who is not a participant.

Repeated expenses involving the same people.

Different participant groups within one case.

Multiple independent cases in one CSV.

Large monetary amounts.

Names containing spaces and Unicode characters.

Invalid CSV columns and malformed rows.

Duplicate participants and invalid monetary amounts.

Cases with multiple possible settlements.



Tests must verify final balances independently.



For suitably small cases, tests must also verify the globally minimum number of payments using an independent reference method or known optimal



