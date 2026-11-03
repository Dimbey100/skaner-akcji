import streamlit as st
import pandas as pd
import numpy as np
import os

# Konfiguracja strony
st.set_page_config(page_title="Skaner Giełdowy", layout="wide", page_icon="📊")
st.title("Skaner Akcji 📊")

@st.cache_data
def wczytaj_i_przetworz_dane():
    # Sprawdzenie czy plik istnieje
    if not os.path.exists("baza_spolek.csv"):
        st.error("Brak pliku 'baza_spolek.csv'. Wgraj wygenerowany plik na GitHub obok skryptu app.py.")
        return pd.DataFrame()
    
    # Wczytanie pliku z zabezpieczeniem przed pustym dokumentem
    try:
        df = pd.read_csv("baza_spolek.csv")
    except pd.errors.EmptyDataError:
        st.error("Plik 'baza_spolek.csv' jest pusty. Wgraj poprawny plik.")
        return pd.DataFrame()

    # Obliczanie CAPE na podstawie dostępnych danych (fallback do P/E jeśli brak 10-letniego zysku)
    if "Sredni_EPS_10_lat" in df.columns:
        df["CAPE_Obliczone"] = df["Cena"] / df["Sredni_EPS_10_lat"]
    else:
        df["CAPE_Obliczone"] = df.get("P/E", np.nan)

    return df

# Wczytanie danych z pliku
df = wczytaj_i_przetworz_dane()

# Jeśli tabela nie jest pusta, wyświetlamy interfejs
if not df.empty:
    # Panel boczny z informacją o wczytanej bazie
    st.sidebar.header("⚙️ Informacje o bazie")
    st.sidebar.success(f"Wczytano spółek: {len(df)}")
    st.sidebar.info("Baza danych ładuje się błyskawicznie z gotowego pliku .csv")

    st.subheader("Filtry Wskaźników")
    
    col1, col2 = st.columns(2)
    
    # Lewa kolumna suwaków
    with col1:
        pe_range = st.slider("P/E (Cena/Zysk)", 0.0, 200.0, (0.0, 30.0))
        cape_range = st.slider("CAPE (Shiller P/E)", 0.0, 200.0, (0.0, 35.0))
        ps_range = st.slider("P/S (Cena/Sprzedaż)", 0.0, 50.0, (0.0, 5.0))
        pbv_range = st.slider("P/BV (Cena/Wartość Księgowa)", 0.0, 50.0, (0.0, 5.0))
        fscore_range = st.slider("F-Score (Piotroski)", 0, 9, (0, 9))
        
    # Prawa kolumna suwaków
    with col2:
        div_range = st.slider("Stopa Dywidendy (%)", 0.0, 30.0, (0.0, 20.0))
        roe_range = st.slider("ROE (%)", -100.0, 300.0, (10.0, 200.0))
        debt_range = st.slider("Zadłużenie/Kapitał", 0.0, 500.0, (0.0, 100.0))
        margin_range = st.slider("Marża Zysku (%)", -50.0, 100.0, (0.0, 100.0))

    # Logika filtrowania z obsługą wartości pustych (NaN)
    filtered_df = df[
        (df.get("P/E", pd.Series(dtype=float)).isna() | df.get("P/E", pd.Series(dtype=float)).between(pe_range[0], pe_range[1])) &
        (df["CAPE_Obliczone"].isna() | df["CAPE_Obliczone"].between(cape_range[0], cape_range[1])) &
        (df.get("P/S", pd.Series(dtype=float)).isna() | df.get("P/S", pd.Series(dtype=float)).between(ps_range[0], ps_range[1])) &
        (df.get("P/BV", pd.Series(dtype=float)).isna() | df.get("P/BV", pd.Series(dtype=float)).between(pbv_range[0], pbv_range[1])) &
        (df.get("Stopa Dywidendy (%)", pd.Series(dtype=float)).isna() | df.get("Stopa Dywidendy (%)", pd.Series(dtype=float)).between(div_range[0], div_range[1])) &
        (df.get("ROE (%)", pd.Series(dtype=float)).isna() | df.get("ROE (%)", pd.Series(dtype=float)).between(roe_range[0], roe_range[1])) &
        (df.get("Zadłużenie/Kapitał", pd.Series(dtype=float)).isna() | df.get("Zadłużenie/Kapitał", pd.Series(dtype=float)).between(debt_range[0], debt_range[1])) &
        (df.get("Marża Zysku (%)", pd.Series(dtype=float)).isna() | df.get("Marża Zysku (%)", pd.Series(dtype=float)).between(margin_range[0], margin_range[1])) &
        (df.get("F-Score", pd.Series(dtype=float)).isna() | df.get("F-Score", pd.Series(dtype=float)).between(fscore_range[0], fscore_range[1]))
    ]
    
    st.success(f"Znaleziono {len(filtered_df)} spółek (z {len(df)} w bazie)")
    
    # Wybór kolumn do wyświetlenia (zabezpieczenie na wypadek braku którejś w pliku CSV)
    docelowe_kolumny = ["Spółka", "Cena", "P/E", "CAPE_Obliczone", "P/S", "P/BV", "Stopa Dywidendy (%)", "ROE (%)", "Zadłużenie/Kapitał", "Marża Zysku (%)", "F-Score"]
    istniejace_kolumny = [kol for kol in docelowe_kolumny if kol in filtered_df.columns]
    
    widok_df = filtered_df[istniejace_kolumny].round(2)
    st.dataframe(widok_df, use_container_width=True, hide_index=True)
