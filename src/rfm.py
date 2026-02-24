import pandas as pd
import numpy as np


def load_data(path):
    df = pd.read_excel(path)
    df = df.dropna(subset=['Customer ID'])
    df['TotalPrice'] = df['Quantity'] * df['Price']
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    return df


def calculate_rfm(df):
    snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

    rfm = df.groupby('Customer ID').agg({
        'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
        'Invoice': 'nunique',
        'TotalPrice': 'sum'
    })

    rfm.columns = ['Recency', 'Frequency', 'Monetary']

    return rfm

if __name__ == "__main__":
    df = load_data("data/online_retail_II.xlsx")
    rfm_table = calculate_rfm(df)
    print(rfm_table.head())
