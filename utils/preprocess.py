import pandas as pd

def load_data(file):
    df = pd.read_csv(file, parse_dates=["날짜"])
    df["구분"] = df["금액"].apply(lambda x: "지출" if x < 0 else "수입")
    df["월"] = df["날짜"].dt.to_period("M")
    return df

def summarize_by_category(df):
    return df[df["구분"]=="지출"].groupby("분류")["금액"].sum().abs().sort_values(ascending=False)

def summarize_by_month(df):
    return df.groupby(["월","구분"])["금액"].sum().unstack().fillna(0)
