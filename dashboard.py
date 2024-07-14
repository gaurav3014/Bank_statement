import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    fig = px.bar(transaction_size_distribution, x=transaction_size_distribution.index, y=transaction_size_distribution.values, 
                 labels={'index': 'Transaction Size', 'y': 'Count'}, title='Transaction Size Distribution')
    st.plotly_chart(fig)
    
    # Transaction Type Frequency
    st.subheader('Frequency of Transaction Types')
    fig = px.bar(transactions_type_count, x=transactions_type_count.index, y=transactions_type_count.values, 
                 labels={'index': 'Transaction Type', 'y': 'Frequency'}, title='Frequency of Transaction Types')
    st.plotly_chart(fig)
    
    # Trend of Account Balance Over Time
    st.subheader('Trend of Account Balance Over Time')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=balances, mode='lines+markers', name='Account Balance'))
    for _, row in significant_changes.iterrows():
        fig.add_annotation(x=row['transactionTimestamp'], y=row['currentBalance'],
                           text=f'Significant Change\n{row["balance_change"]:.2f}', showarrow=True, arrowhead=1)
    fig.update_layout(title='Trend of Account Balance Over Time', xaxis_title='Date', yaxis_title='Account Balance')
    st.plotly_chart(fig)
    
    # Frequency and Amount of Spending by Transaction Mode
    st.subheader('Frequency and Amount of Spending by Transaction Mode')
    modes = list(categories.keys())
    amounts = [categories[mode]['amount'] for mode in modes]
    frequencies = [categories[mode]['frequency'] for mode in modes]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=modes, y=amounts, name='Total Amount ($)', marker_color='blue'))
    fig.add_trace(go.Scatter(x=modes, y=frequencies, mode='lines+markers', name='Frequency', yaxis='y2', marker_color='red'))
    fig.update_layout(title='Frequency and Amount of Spending by Transaction Mode',
                      xaxis_title='Transaction Mode',
                      yaxis_title='Total Amount ($)',
                      yaxis2=dict(title='Frequency', overlaying='y', side='right'))
    st.plotly_chart(fig)
    
    # Income Transactions Over Time
    st.subheader('Income Transactions Over Time')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=income_timestamps, y=income_amounts, mode='markers', name='Income Amount'))
    fig.update_layout(title='Income Transactions Over Time', xaxis_title='Date', yaxis_title='Income Amount ($)')
    st.plotly_chart(fig)
    
    # Display analysis on income patterns
    st.write("The data shows income transactions over time. There is no clear trend, but there might be seasonality with peaks in December and January.")
else:
    st.error("Failed to load transactions data.")
