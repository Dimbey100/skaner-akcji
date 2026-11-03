import streamlit as st
import pandas as pd
import numpy as np
import os

# Konfiguracja strony
st.set_page_config(page_title="Skaner Giełdowy", layout="wide", page_icon="📊")
st.title("Globalny Skaner Akcji 📊")

@st.cache_data
def wczytaj_i_przetworz_dane():
    df_lista = []
    
    # Próba wczytania bazy S&P 500
    if os.path.exists("sp500_baza.csv"):
        try:
            df_lista.append(pd.read_csv("sp500_baza.csv"))
        except pd.errors.EmptyDataError:
            st.warning("Plik 'sp500_baza.csv' jest pusty.")
            
    # Próba wczytania bazy GPW
    if os.path.exists("gpw_baza.csv"):
        try:
            df_lista.append(pd.read_csv("gpw_baza.csv"))
        except pd.errors.EmptyDataError:
            st.warning("Plik 'gpw_baza.csv' jest pusty.")

    # Połączenie obu baz, jeśli istnieją
    if not df_lista:
        st.error("Brak plików z bazami danych. Wgraj 'sp500_baza.csv' oraz 'gpw_baza.csv' na GitHub.")
        return pd.DataFrame()
        
    df = pd.concat(df_lista, ignore_index=True)

    # Obliczanie CAPE (fallback do P/E jeśli brak długiej historii)
    if "Sredni_EPS_10_lat" in df.columns:
        df["CAPE_Obliczone"] = df["Cena"] / df["Sredni_EPS_10_lat"]
    else:
        df["CAPE_Obliczone"] = df.get("P/E", np.nan)

    return df

# Wczytanie połączonych danych z plików
df = wczytaj_i_przetworz_dane()

if not df.empty:
    # --- PANEL BOCZNY: WYBÓR RYNKU ---
    st.sidebar.header("⚙️ Opcje Skanera")
    st.sidebar.success(f"Wczytano łącznie: {len(df)} spółek")
    
    wybrany_rynek = st.sidebar.radio(
        "Wybierz koszyk spółek do skanowania:",
        ["Wszystkie (USA + Polska)", "Tylko S&P 500 (USA)", "Tylko GPW (Polska)"]
    )
    
    # Filtrowanie wstępne po rynku
    if wybrany_rynek == "Tylko S&P 500 (USA)":
        df = df[df["Rynek"] == "S&P 500 (USA)"]
    elif wybrany_rynek == "Tylko GPW (Polska)":
        df = df[df["Rynek"] == "GPW (Polska)"]

    st.subheader(f"Filtry Wskaźników: {wybrany_rynek}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pe_range = st.slider("P/E (Cena/Zysk)", 0.0, 200.0, (0.0, 30.0))
        cape_range = st.slider("CAPE (Shiller P/E)", 0.0, 200.0, (0.0, 35.0))
        ps_range = st.slider("P/S (Cena/Sprzedaż)", 0.0, 50.0, (0.0, 5.0))
        pbv_range = st.slider("P/BV (Cena/Wartość Księgowa)", 0.0, 50.0, (0.0, 5.0))
        fscore_range = st.slider("F-Score (Piotroski)", 0, 9, (0, 9))
        
    with col2:
        div_range = st.slider("Stopa Dywidendy (%)", 0.0, 30.0, (0.0, 20.0))
        roe_range = st.slider("ROE (%)", -100.0, 300.0, (10.0, 200.0))
        debt_range = st.slider("Zadłużenie/Kapitał", 0.0, 500.0, (0.0, 100.0))
        margin_range = st.slider("Marża Zysku (%)", -50.0, 100.0, (0.0, 100.0))

    # Główna logika filtrowania skanera
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
    
    st.success(f"Znaleziono {len(filtered_df)} spółek spełniających kryteria w tym koszyku (z {len(df)})")
    
    docelowe_kolumny = ["Spółka", "Rynek", "Cena", "P/E", "CAPE_Obliczone", "P/S", "P/BV", "Stopa Dywidendy (%)", "ROE (%)", "Zadłużenie/Kapitał", "Marża Zysku (%)", "F-Score"]
    istniejace_kolumny = [kol for kol in docelowe_kolumny if kol in filtered_df.columns]
    
    widok_df = filtered_df[istniejace_kolumny].round(2)
    st.dataframe(widok_df, use_container_width=True, hide_index=True)
