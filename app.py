import streamlit as st
import yfinance as yf
import pandas as pd

# Konfiguracja strony pod telefony (ukrywa niepotrzebne marginesy)
st.set_page_config(page_title="Skaner Giełdowy", layout="centered")

st.title("Skaner Akcji 📈")

# Pobieranie danych (cache zapobiega pobieraniu przy każdym przesunięciu suwaka)
@st.cache_data(ttl=3600)
def get_data():
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "JNJ", "PFE", "KO"]
    data = []
    for t in tickers:
        stock = yf.Ticker(t)
        info = stock.info
        data.append({
            "Spółka": t,
            "Cena": info.get("currentPrice", 0),
            "P/E": info.get("trailingPE", 0),
            "Zadłużenie/Kapitał": info.get("debtToEquity", 0)
        })
    return pd.DataFrame(data)

df = get_data()

# Interfejs użytkownika (suwaki)
st.subheader("Filtry")
max_pe = st.slider("Maksymalne P/E (Cena do Zysku)", min_value=5.0, max_value=100.0, value=25.0)
max_debt = st.slider("Maksymalne Zadłużenie (Debt/Equity)", min_value=0.0, max_value=200.0, value=100.0)

# Logika filtrowania
filtered_df = df[(df["P/E"] > 0) & (df["P/E"] <= max_pe) & (df["Zadłużenie/Kapitał"] <= max_debt)]

# Wyświetlanie wyników
st.subheader(f"Znalezione spółki: {len(filtered_df)}")
st.dataframe(filtered_df, use_container_width=True)