import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Skaner Giełdowy", layout="wide", page_icon="📊")
st.title("Globalny Skaner Akcji 📊")

def oblicz_cape(df):
    if "Sredni_EPS_10_lat" in df.columns:
        return df["Cena"] / df["Sredni_EPS_10_lat"]
    return np.nan

def oblicz_f_score(row):
    wymagane_kolumny = [
        "ROA", "CFO", "ROA_poprzedni", "Zadłużenie_Długoterminowe", 
        "Zadłużenie_poprzednie", "Current_Ratio", "Current_Ratio_poprzednie",
        "Liczba_Akcji", "Liczba_Akcji_poprzednia", "Gross_Margin", 
        "Gross_Margin_poprzednia", "Asset_Turnover", "Asset_Turnover_poprzedni"
    ]
    
    for kol in wymagane_kolumny:
        if kol not in row.index or pd.isna(row.get(kol)):
            return np.nan

    score = 0
    if row["ROA"] > 0: score += 1
    if row["CFO"] > 0: score += 1
    if row["ROA"] > row["ROA_poprzedni"]: score += 1
    if row["CFO"] > row["ROA"]: score += 1
    
    if row["Zadłużenie_Długoterminowe"] < row["Zadłużenie_poprzednie"]: score += 1
    if row["Current_Ratio"] > row["Current_Ratio_poprzednie"]: score += 1
    if row["Liczba_Akcji"] <= row["Liczba_Akcji_poprzednia"]: score += 1
    
    if row["Gross_Margin"] > row["Gross_Margin_poprzednia"]: score += 1
    if row["Asset_Turnover"] > row["Asset_Turnover_poprzedni"]: score += 1
    
    return score

@st.cache_data
def wczytaj_i_przetworz_dane():
    df_lista = []
    
    if os.path.exists("sp500_baza.csv"):
        try: df_lista.append(pd.read_csv("sp500_baza.csv"))
        except pd.errors.EmptyDataError: st.warning("Plik 'sp500_baza.csv' jest pusty.")
            
    if os.path.exists("gpw_baza.csv"):
        try: df_lista.append(pd.read_csv("gpw_baza.csv"))
        except pd.errors.EmptyDataError: st.warning("Plik 'gpw_baza.csv' jest pusty.")

    if not df_lista:
        st.error("Brak plików z bazami danych. Wgraj 'sp500_baza.csv' oraz 'gpw_baza.csv'.")
        return pd.DataFrame()
        
    df = pd.concat(df_lista, ignore_index=True)

    df["CAPE_Obliczone"] = oblicz_cape(df)
    if "F-Score" not in df.columns or df["F-Score"].isna().all():
        df["F-Score"] = df.apply(oblicz_f_score, axis=1)

    return df

df = wczytaj_i_przetworz_dane()

# Funkcja pomocnicza do tworzenia estetycznych pól MIN/MAX
def stworz_zakres(nazwa, min_def, max_def, krok=1.0, typ=float):
    st.markdown(f"**{nazwa}**")
    c1, c2 = st.columns(2)
    v_min = c1.number_input("MIN", value=typ(min_def), step=typ(krok), key=f"{nazwa}_min")
    v_max = c2.number_input("MAX", value=typ(max_def), step=typ(krok), key=f"{nazwa}_max")
    return v_min, v_max

if not df.empty:
    st.sidebar.header("⚙️ Opcje Skanera")
    st.sidebar.success(f"Wczytano łącznie: {len(df)} spółek")
    
    wybrany_rynek = st.sidebar.radio(
        "Wybierz koszyk spółek:",
        ["Wszystkie (USA + Polska)", "Tylko S&P 500 (USA)", "Tylko GPW (Polska)"]
    )
    
    if wybrany_rynek == "Tylko S&P 500 (USA)": df = df[df["Rynek"] == "S&P 500 (USA)"]
    elif wybrany_rynek == "Tylko GPW (Polska)": df = df[df["Rynek"] == "GPW (Polska)"]

    st.subheader("Wpisz zakresy (MIN i MAX)")
    
    colA, colB = st.columns(2)
    
    with colA:
        pe_min, pe_max = stworz_zakres("P/E (Cena/Zysk)", 0.0, 30.0)
        cape_min, cape_max = stworz_zakres("CAPE (Shiller P/E)", 0.0, 35.0)
        ps_min, ps_max = stworz_zakres("P/S (Cena/Sprzedaż)", 0.0, 5.0)
        pbv_min, pbv_max = stworz_zakres("P/BV (Wartość Księgowa)", 0.0, 5.0)
        fscore_min, fscore_max = stworz_zakres("F-Score (Piotroski)", 0, 9, krok=1, typ=int)
        
    with colB:
        div_min, div_max = stworz_zakres("Stopa Dywidendy (%)", 0.0, 20.0)
        roe_min, roe_max = stworz_zakres("ROE (%)", 10.0, 200.0)
        debt_min, debt_max = stworz_zakres("Zadłużenie/Kapitał", 0.0, 100.0)
        margin_min, margin_max = stworz_zakres("Marża Zysku (%)", 0.0, 100.0)

    # Logika filtrowania z obsługą braków danych (NaN)
    filtered_df = df[
        (df.get("P/E", pd.Series(dtype=float)).isna() | df.get("P/E", pd.Series(dtype=float)).between(pe_min, pe_max)) &
        (df["CAPE_Obliczone"].isna() | df["CAPE_Obliczone"].between(cape_min, cape_max)) &
        (df.get("P/S", pd.Series(dtype=float)).isna() | df.get("P/S", pd.Series(dtype=float)).between(ps_min, ps_max)) &
        (df.get("P/BV", pd.Series(dtype=float)).isna() | df.get("P/BV", pd.Series(dtype=float)).between(pbv_min, pbv_max)) &
        (df.get("Stopa Dywidendy (%)", pd.Series(dtype=float)).isna() | df.get("Stopa Dywidendy (%)", pd.Series(dtype=float)).between(div_min, div_max)) &
        (df.get("ROE (%)", pd.Series(dtype=float)).isna() | df.get("ROE (%)", pd.Series(dtype=float)).between(roe_min, roe_max)) &
        (df.get("Zadłużenie/Kapitał", pd.Series(dtype=float)).isna() | df.get("Zadłużenie/Kapitał", pd.Series(dtype=float)).between(debt_min, debt_max)) &
        (df.get("Marża Zysku (%)", pd.Series(dtype=float)).isna() | df.get("Marża Zysku (%)", pd.Series(dtype=float)).between(margin_min, margin_max)) &
        (df["F-Score"].isna() | df["F-Score"].between(fscore_min, fscore_max))
    ]
    
    st.success(f"Znaleziono {len(filtered_df)} spółek spełniających kryteria w tym koszyku (z {len(df)})")
    
    docelowe_kolumny = ["Spółka", "Rynek", "Cena", "P/E", "CAPE_Obliczone", "P/S", "P/BV", "Stopa Dywidendy (%)", "ROE (%)", "Zadłużenie/Kapitał", "Marża Zysku (%)", "F-Score"]
    istniejace_kolumny = [kol for kol in docelowe_kolumny if kol in filtered_df.columns]
    
    widok_df = filtered_df[istniejace_kolumny].round(2)
    st.dataframe(widok_df, use_container_width=True, hide_index=True)
