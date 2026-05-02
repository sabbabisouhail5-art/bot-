import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📊 Trading Bot Dashboard")

auto_refresh = st.checkbox("Auto refresh", value=True)

if auto_refresh:
    time.sleep(2)
    st.rerun()

df = pd.read_csv("trades.csv")

st.subheader("Last 10 Trades")
st.dataframe(df.tail(10), use_container_width=True)

sell_df = df[df["Action"].astype(str).str.contains("SELL", na=False)].copy()
sell_df["Profit"] = pd.to_numeric(sell_df["Profit"], errors="coerce")
sell_df = sell_df.dropna(subset=["Profit"])

total_profit = sell_df["Profit"].sum()
wins = len(sell_df[sell_df["Profit"] > 0])
losses = len(sell_df[sell_df["Profit"] < 0])
total_trades = len(sell_df)
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Profit", f"{total_profit:.2f} USDT")
col2.metric("Wins", wins)
col3.metric("Losses", losses)
col4.metric("Win Rate", f"{win_rate:.1f}%")

st.caption(f"Total SELL Trades: {win_rate}")

sell_df["Cumulative Profit"] = sell_df["Profit"].cumsum()

st.subheader("Cumulative Profit Graph")
st.line_chart(sell_df["Cumulative Profit"])
