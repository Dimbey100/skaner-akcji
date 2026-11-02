import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
import os
import requests
from io import StringIO

# Konfiguracja strony
st.set_page_config(page_title="Skaner Giełdowy", layout="wide", page_icon="📊")
st.title("Skaner Akcji 📊")

# --- FUNKCJE POBIERAJĄCE DANE ---

def get_sp500_tickers(limit=None):
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # Przedstawiamy się jako przeglądarka Chrome, żeby Wikipedia nas nie zablokowała
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    # Nowe wersje pandas wymagają opakowania tekstu w StringIO
    tables = pd.read_html(StringIO(response.text))
    
    tickers = tables[0]['Symbol'].str.replace('.', '-').tolist()
    
    if limit:
        return tickers[:limit]
    return tickers

def pobierz_baze(limit_spolek, progress_bar, status_text):
    tickers = get_sp500_tickers(limit_spolek)
    data = []
    total = len(tickers)
    
    for i, t in enumerate(tickers):
        # Aktualizacja tekstu w aplikacji na żywo
        status_text.text(f"Pobieranie {i+1}/{total} : {t}...")
        
        try:
            stock = yf.Ticker(t)
            info = stock.info
            
            if info and "symbol" in info:
                pe = info.get("trailingPE", np.nan)
                ps = info.get("priceToSalesTrailing12Months", np.nan)
                pbv = info.get("priceToBook", np.nan)
                
                div = info.get("dividendYield")
                div_yield = div * 100 if div is not None else 0.0
                
                roe_val = info.get("returnOnEquity")
                roe = roe_val * 100 if roe_val is not None else np.nan
                
                debt_eq = info.get("debtToEquity", np.nan)
                
                margin_val = info.get("profitMargins")
                margin = margin_val * 100 if margin_val is not None else np.nan

                data.append({
                    "Spółka": t,
                    "Cena": info.get("currentPrice", np.nan),
                    "P/E": pe,
                    "P/S": ps,
                    "P/BV": pbv,
                    "Stopa Dywidendy (%)": div_yield,
                    "ROE (%)": roe,
                    "Zadłużenie/Kapitał": debt_eq,
                    "Marża Zysku (%)": margin,
                    "F-Score": np.nan, 
                    "CAPE": np.nan     
                })
        except Exception:
            pass # Ignorujemy błędy połączenia dla pojedynczych spółek
            
        time.sleep(0.2) # Zabezpieczenie przed banem od Yahoo
        progress_bar.progress((i + 1) / total) # Pasek postępu rośnie
        
        # Opcjonalny autozapis w trakcie co 50 spółek
        if (i + 1) % 50 == 0:
            pd.DataFrame(data).to_csv("baza_spolek.csv", index=False)

    # Zapis końcowy wszystkich pobranych danych
    df = pd.DataFrame(data)
    df.to_csv("baza_spolek.csv", index=False)
    
    # Czyszczenie pamięci podręcznej (aby skaner od razu wczytał nowe dane)
    st.cache_data.clear()
    status_text.success("✅ Baza została poprawnie pobrana i zaktualizowana!")
    time.sleep(2) # Pokazuj komunikat sukcesu przez 2 sekundy
    st.rerun() # Automatyczne odświeżenie strony

# --- FUNKCJE SKANERA ---

@st.cache_data
def wczytaj_i_przetworz_dane():
    if not os.path.exists("baza_spolek.csv"):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv("baza_spolek.csv")
    except pd.errors.EmptyDataError:
        # Zabezpieczenie przed błędem, gdy plik istnieje, ale ma 0 bajtów
        st.error("Plik bazy danych jest pusty. Pobierz bazę ponownie z panelu bocznego.")
        return pd.DataFrame()
    
    # Obliczanie CAPE na podstawie dostępnych danych jako fallback
    if "Sredni_EPS_10_lat" in df.columns:
        df["CAPE_Obliczone"] = df["Cena"] / df["Sredni_EPS_10_lat"]
    else:
        df["CAPE_Obliczone"] = df.get("P/E", np.nan)

    return df


    
    

# --- INTERFEJS UŻYTKOWNIKA ---

# 1. PANEL BOCZNY (ZARZĄDZANIE BAZĄ)
st.sidebar.header("⚙️ Baza danych")

if os.path.exists("baza_spolek.csv"):
    czas_modyfikacji = time.ctime(os.path.getmtime("baza_spolek.csv"))
    st.sidebar.success(f"Baza istnieje. Ostatnia aktualizacja:\n{czas_modyfikacji}")
else:
    st.sidebar.error("Brak bazy danych. Musisz ją najpierw pobrać!")

st.sidebar.markdown("---")
ile_pobrac = st.sidebar.radio("Ile spółek pobrać?", ["Szybki test (50 spółek)", "Całe S&P 500 (500 spółek)"])
limit = 50 if "test" in ile_pobrac else None

if st.sidebar.button("🔄 Pobierz/Aktualizuj Bazę", use_container_width=True):
    st.sidebar.info("Rozpoczęto pobieranie...")
    # Puste kontenery (zostaną nadpisane przez funkcję)
    prog_bar = st.sidebar.progress(0)
    stat_text = st.sidebar.empty()
    pobierz_baze(limit, prog_bar, stat_text)

# 2. GŁÓWNY SKANER
df = wczytaj_i_przetworz_dane()

if not df.empty:
    st.subheader("Filtry Wskaźników")
    col1, col2 = st.columns(2)
    
    with col1:
        pe_range = st.slider("P/E (Cena/Zysk)", 0.0, 200.0, (0.0, 30.0))
        cape_range = st.slider("CAPE (Shiller P/E)", 0.0, 200.0, (0.0, 35.0))
        ps_range = st.slider("P/S (Cena/Sprzedaż)", 0.0, 50.0, (0.0, 5.0))
        pbv_range = st.slider("P/BV (Cena/Wartość Księgowa)", 0.0, 50.0, (0.0, 5.0))
        
    with col2:
        div_range = st.slider("Stopa Dywidendy (%)", 0.0, 30.0, (0.0, 20.0))
        roe_range = st.slider("ROE (%)", -100.0, 300.0, (10.0, 200.0))
        debt_range = st.slider("Zadłużenie/Kapitał", 0.0, 500.0, (0.0, 100.0))

    # Filtrowanie
    filtered_df = df[
        (df["P/E"].isna() | df["P/E"].between(pe_range[0], pe_range[1])) &
        (df["CAPE_Obliczone"].isna() | df["CAPE_Obliczone"].between(cape_range[0], cape_range[1])) &
        (df["P/S"].isna() | df["P/S"].between(ps_range[0], ps_range[1])) &
        (df["P/BV"].isna() | df["P/BV"].between(pbv_range[0], pbv_range[1])) &
        (df["Stopa Dywidendy (%)"].isna() | df["Stopa Dywidendy (%)"].between(div_range[0], div_range[1])) &
        (df["ROE (%)"].isna() | df["ROE (%)"].between(roe_range[0], roe_range[1])) &
        (df["Zadłużenie/Kapitał"].isna() | df["Zadłużenie/Kapitał"].between(debt_range[0], debt_range[1]))
    ]
    
    st.success(f"Znaleziono {len(filtered_df)} spółek (z {len(df)} w bazie)")
    
    # Formatowanie kolumn przed wyświetleniem
    widok_df = filtered_df[["Spółka", "Cena", "P/E", "CAPE_Obliczone", "P/S", "P/BV", "Stopa Dywidendy (%)", "ROE (%)", "Zadłużenie/Kapitał"]].round(2)
    st.dataframe(widok_df, use_container_width=True, hide_index=True)
else:
    st.info("👈 Użyj przycisku w menu bocznym, aby wygenerować bazę danych.")
