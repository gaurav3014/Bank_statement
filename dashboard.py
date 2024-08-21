import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime
from collections import defaultdict

# Load data
def load_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data['Account']['Transactions']['Transaction']
    except FileNotFoundError:
        st.error(f"File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decoding JSON from file {file_path}.")
        return None

transactions = load_data('P1- BankStatements.json')
if transactions is not None:
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
    transaction_size_distribution.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_xlabel('Transaction Size')
    ax.set_ylabel('Count')
    ax.set_title('Transaction Size Distribution')
    st.pyplot(fig)
    
    # Transaction Type Frequency
    st.subheader('Frequency of Transaction Types')
    fig, ax = plt.subplots()
    transactions_type_count.plot(kind='bar', ax=ax, color='lightgreen')
    ax.set_xlabel('Transaction Type')
    ax.set_ylabel('Frequency')
    ax.set_title('Frequency of Transaction Types')
    st.pyplot(fig)
    
    # Trend of Account Balance Over Time
    st.subheader('Trend of Account Balance Over Time')
    fig, ax = plt.subplots()
    ax.plot(timestamps, balances, marker='o', linestyle='-')
    for _, row in significant_changes.iterrows():
        ax.annotate(f'Significant Change\n{row["balance_change"]:.2f}', 
                    xy=(row['transactionTimestamp'], row['currentBalance']),
                    xytext=(row['transactionTimestamp'], row['currentBalance'] + 1000),
                    arrowprops=dict(facecolor='red', shrink=0.05))
    ax.set_xlabel('Date')
    ax.set_ylabel('Account Balance')
    ax.set_title('Trend of Account Balance Over Time')
    st.pyplot(fig)
    
    # Frequency and Amount of Spending by Transaction Mode
    st.subheader('Frequency and Amount of Spending by Transaction Mode')
    modes = list(categories.keys())
    amounts = [categories[mode]['amount'] for mode in modes]
    frequencies = [categories[mode]['frequency'] for mode in modes]
    
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.bar(modes, amounts, color='blue', alpha=0.6, label='Total Amount ($)')
    ax2.plot(modes, frequencies, color='red', marker='o', label='Frequency', linestyle='-')
    ax1.set_xlabel('Transaction Mode')
    ax1.set_ylabel('Total Amount ($)', color='blue')
    ax2.set_ylabel('Frequency', color='red')
    ax1.set_title('Frequency and Amount of Spending by Transaction Mode')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    st.pyplot(fig)
    
    # Income Transactions Over Time
    st.subheader('Income Transactions Over Time')
    fig, ax = plt.subplots()
    ax.scatter(income_timestamps, income_amounts, color='purple')
    ax.set_xlabel('Date')
    ax.set_ylabel('Income Amount ($)')
    ax.set_title('Income Transactions Over Time')
    st.pyplot(fig)
    
    # Display analysis on income patterns
    st.write("The data shows income transactions over time. There is no clear trend, but there might be seasonality with peaks in December and January.")
else:
    st.error("Failed to load transactions data.")
