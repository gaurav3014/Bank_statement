import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime
from collections import defaultdict

# Load data
with open('P1- BankStatements.json', 'r') as file:
    data = json.load(file)

# Extract transactions and create DataFrame
transactions = data['Account']['Transactions']['Transaction']
df = pd.DataFrame(transactions)

# Convert columns to appropriate data types
df['amount'] = df['amount'].astype(float)
df['currentBalance'] = df['currentBalance'].astype(float)
df['transactionTimestamp'] = pd.to_datetime(df['transactionTimestamp'])
df['valueDate'] = pd.to_datetime(df['valueDate'])

# Calculate summary statistics and other metrics
total_transactions = len(df)
largest_transaction = df['amount'].max()
summary_stats = df['amount'].describe()
small_threshold = 500
df['transaction_size'] = df['amount'].apply(lambda x: 'small' if x < small_threshold else 'large')
transaction_size_distribution = df['transaction_size'].value_counts()
transactions_type_count = df['type'].value_counts()
df = df.sort_values(by='transactionTimestamp')
timestamps = df['transactionTimestamp']
balances = df['currentBalance']
df['balance_change'] = df['currentBalance'].diff().abs()
significant_changes = df[df['balance_change'] > df['balance_change'].mean() + 2 * df['balance_change'].std()]

# Categorize transactions and compute the total amount and frequency in each category
categories = defaultdict(lambda: {'amount': 0, 'frequency': 0})
for transaction in transactions:
    mode = transaction['mode']
    amount = float(transaction['amount'])
    if transaction['type'] == 'DEBIT':
        categories[mode]['amount'] += amount
        categories[mode]['frequency'] += 1
categories = dict(categories)

# Extract timestamps and amounts for income transactions
income_transactions = [txn for txn in transactions if txn['type'] == 'CREDIT']
income_timestamps = [datetime.fromisoformat(txn['transactionTimestamp'].replace('T', ' ').replace('+05:30', '')) for txn in income_transactions]
income_amounts = [float(txn['amount']) for txn in income_transactions]

# Streamlit App
st.set_page_config(layout="wide")

st.title('Bank Statement Analysis Dashboard')

# Summary Section
st.header('Summary Statistics')
col1, col2, col3 = st.columns(3)
col1.metric("Total Transactions", total_transactions)
col2.metric("Largest Transaction", f"${largest_transaction:,.2f}")
col3.metric("Average Transaction", f"${summary_stats['mean']:,.2f}")

# Transaction Size Distribution
st.subheader('Transaction Size Distribution')
fig, ax = plt.subplots()
transaction_size_distribution.plot(kind='bar', color=['skyblue', 'lightgreen'], ax=ax)
ax.set_title('Transaction Size Distribution')
ax.set_xlabel('Transaction Size')
ax.set_ylabel('Count')
for i in range(len(transaction_size_distribution)):
    ax.text(i, transaction_size_distribution[i] + 5, str(transaction_size_distribution[i]), ha='center')
st.pyplot(fig)

# Transaction Type Frequency
st.subheader('Frequency of Transaction Types')
fig, ax = plt.subplots()
transactions_type_count.plot(kind='bar', color=['skyblue', 'lightgreen'], ax=ax)
ax.set_title('Frequency of Transaction Types')
ax.set_xlabel('Transaction Type')
ax.set_ylabel('Frequency')
for i in range(len(transactions_type_count)):
    ax.text(i, transactions_type_count[i] + 5, str(transactions_type_count[i]), ha='center')
st.pyplot(fig)

# Trend of Account Balance Over Time
st.subheader('Trend of Account Balance Over Time')
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(timestamps, balances, marker='o', label='Account Balance')
ax.set_xlabel('Date')
ax.set_ylabel('Account Balance')
ax.set_title('Trend of Account Balance Over Time')
ax.tick_params(axis='x', rotation=45)
for _, row in significant_changes.iterrows():
    ax.annotate(f'Significant Change\n{row["balance_change"]:.2f}', xy=(row['transactionTimestamp'], row['currentBalance']),
                xytext=(15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='->', color='red'))
plt.tight_layout()
st.pyplot(fig)

# Frequency and Amount of Spending by Transaction Mode
st.subheader('Frequency and Amount of Spending by Transaction Mode')
modes = list(categories.keys())
amounts = [categories[mode]['amount'] for mode in modes]
frequencies = [categories[mode]['frequency'] for mode in modes]

fig, ax1 = plt.subplots()
color = 'tab:blue'
ax1.set_xlabel('Transaction Mode')
ax1.set_ylabel('Total Amount ($)', color=color)
ax1.bar(modes, amounts, color=color, alpha=0.6)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Frequency', color=color)
ax2.plot(modes, frequencies, color=color, marker='o')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.title('Frequency and Amount of Spending by Transaction Mode')
st.pyplot(fig)

# Income Transactions Over Time
st.subheader('Income Transactions Over Time')
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(income_timestamps, income_amounts, marker='o', linestyle='None')
ax.set_xlabel('Date')
ax.set_ylabel('Income Amount ($)')
ax.set_title('Income Transactions Over Time')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig)

# Display analysis on income patterns
st.write("The data shows income transactions over time. There is no clear trend, but there might be seasonality with peaks in December and January.")
