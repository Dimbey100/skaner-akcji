import streamlit as st
import pandas as pd
import numpy as np
import os
import json

st.set_page_config(page_title="Skaner Giełdowy", layout="wide", page_icon="📊")
st.title("Globalny Skaner Akcji 📊")

# --- ZAPIS ULUBIONYCH DO PLIKU ---
def wczytaj_ulubione():
    if os.path.exists("ulubione.json"):
        try:
            with open("ulubione.json", "r") as f:
                return json.load(f)
        except:
            return []
    return []

def zapisz_ulubione():
    with open("ulubione.json", "w") as f:
        json.dump(st.session_state["moje_ulubione_widget"], f)

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
    if row.get("ROA", 0) > 0: score += 1
    if row.get("CFO", 0) > 0: score += 1
    if row.get("ROA", 0) > row.get("ROA_poprzedni", 0): score += 1
    if row.get("CFO", 0) > row.get("ROA", 0): score += 1
    
    if row.get("Zadłużenie_Długoterminowe", 0) < row.get("Zadłużenie_poprzednie", 0): score += 1
    if row.get("Current_Ratio", 0) > row.get("Current_Ratio_poprzednie", 0): score += 1
    if row.get("Liczba_Akcji", 0) <= row.get("Liczba_Akcji_poprzednia", 0): score += 1
    
    if row.get("Gross_Margin", 0) > row.get("Gross_Margin_poprzednia", 0): score += 1
    if row.get("Asset_Turnover", 0) > row.get("Asset_Turnover_poprzedni", 0): score += 1
    return score

@st.cache_data
def wczytaj_i_przetworz_dane():
    df_lista = []
    # Lista wszystkich baz danych, łącznie z nowymi rynkami
    pliki_baz = [
        "sp500_baza.csv", 
        "gpw_baza.csv", 
        "europa_baza.csv", 
        "azja_baza.csv",
        "latam_baza.csv",
        "indie_baza.csv"
    ]
    
    for plik in pliki_baz:
        if os.path.exists(plik):
            try: 
                df_lista.append(pd.read_csv(plik))
            except pd.errors.EmptyDataError: 
                st.warning(f"Plik '{plik}' jest pusty.")
        else:
            st.warning(f"Brak pliku '{plik}'. Wgraj go na GitHub, aby rozszerzyć skaner.")

    if not df_lista:
        st.error("Brak jakichkolwiek plików z bazami danych. Wgraj pliki CSV.")
        return pd.DataFrame()
        
    df = pd.concat(df_lista, ignore_index=True)
    
    if "Zadłużenie/Kapitał" in df.columns and "Zadłużenie/Kapitał (%)" not in df.columns:
        df.rename(columns={"Zadłużenie/Kapitał": "Zadłużenie/Kapitał (%)"}, inplace=True)

    df["CAPE_Obliczone"] = oblicz_cape(df)
    if "F-Score" not in df.columns or df["F-Score"].isna().all():
        df["F-Score"] = df.apply(oblicz_f_score, axis=1)

    return df

def stworz_zakres(nazwa, min_def, max_def, krok=1.0, typ=float):
    st.markdown("---")
    wlaczone = st.checkbox(f"Użyj filtru: {nazwa}", value=False, key=f"{nazwa}_check")
    c1, c2 = st.columns(2)
    v_min = c1.number_input("MIN", value=typ(min_def), step=typ(krok), key=f"{nazwa}_min", disabled=not wlaczone)
    v_max = c2.number_input("MAX", value=typ(max_def), step=typ(krok), key=f"{nazwa}_max", disabled=not wlaczone)
    return wlaczone, v_min, v_max

df = wczytaj_i_przetworz_dane()

if not df.empty:
    st.sidebar.header("⚙️ Opcje Skanera")
    st.sidebar.success(f"Wczytano łącznie: {len(df)} spółek")
    
    # Rozszerzone menu wyboru rynku
    opcje_rynkow = [
        "Wszystkie Rynki", 
        "S&P 500 (USA)", 
        "GPW (Polska)", 
        "Europa Zachodnia", 
        "Azja",
        "Ameryka Południowa",
        "Indie"
    ]
    wybrany_rynek = st.sidebar.radio("Wybierz koszyk spółek:", opcje_rynkow)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⭐ Ulubione Spółki")
    
    wszystkie_symbole = sorted(df["Spółka"].astype(str).tolist())
    
    if 'ulubione' not in st.session_state:
        st.session_state['ulubione'] = wczytaj_ulubione()
        
    bezpieczne_ulubione = [s for s in st.session_state['ulubione'] if s in wszystkie_symbole]
    
    wybrane_spolki = st.sidebar.multiselect(
        "Dodaj spółki do obserwowanych:",
        options=wszystkie_symbole,
        default=bezpieczne_ulubione,
        help="Wpisz lub wybierz z listy nazwy/skróty spółek, które chcesz śledzić.",
        key="moje_ulubione_widget",
        on_change=zapisz_ulubione
    )
    
    st.session_state['ulubione'] = wybrane_spolki
    
    pokaz_tylko_ulubione = st.sidebar.checkbox("👁️ Pokazuj TYLKO moje ulubione spółki", value=False)
    
    # Filtrowanie po wybranym rynku
    if wybrany_rynek != "Wszystkie Rynki": 
        df = df[df["Rynek"] == wybrany_rynek]

    if pokaz_tylko_ulubione:
        df = df[df["Spółka"].isin(st.session_state['ulubione'])]
        if df.empty:
            st.warning("Nie masz żadnych ulubionych spółek w tym koszyku lub lista jest pusta.")

    st.subheader("Filtry Wskaźników")
    colA, colB = st.columns(2)
    
    with colA:
        pe_wl, pe_min, pe_max = stworz_zakres("P/E (Cena/Zysk)", 0.0, 30.0)
        cape_wl, cape_min, cape_max = stworz_zakres("CAPE (Shiller P/E)", 0.0, 35.0)
        ps_wl, ps_min, ps_max = stworz_zakres("P/S (Cena/Sprzedaż)", 0.0, 5.0)
        pbv_wl, pbv_min, pbv_max = stworz_zakres("P/BV (Wartość Księgowa)", 0.0, 5.0)
        fscore_wl, fscore_min, fscore_max = stworz_zakres("F-Score (Piotroski)", 0, 9, krok=1, typ=int)
        
    with colB:
        div_wl, div_min, div_max = stworz_zakres("Stopa Dywidendy (%)", 0.0, 15.0)
        roe_wl, roe_min, roe_max = stworz_zakres("ROE (%)", 10.0, 100.0)
        debt_wl, debt_min, debt_max = stworz_zakres("Zadłużenie/Kapitał (%)", 0.0, 200.0)
        margin_wl, margin_min, margin_max = stworz_zakres("Marża Zysku (%)", 0.0, 50.0)

    mask = pd.Series(True, index=df.index)
    
    if pe_wl: mask &= (df["P/E"].isna() | df["P/E"].between(pe_min, pe_max))
    if cape_wl: mask &= (df["CAPE_Obliczone"].isna() | df["CAPE_Obliczone"].between(cape_min, cape_max))
    if ps_wl: mask &= (df["P/S"].isna() | df["P/S"].between(ps_min, ps_max))
    if pbv_wl: mask &= (df["P/BV"].isna() | df["P/BV"].between(pbv_min, pbv_max))
    if fscore_wl: mask &= (df["F-Score"].isna() | df["F-Score"].between(fscore_min, fscore_max))
    if div_wl: mask &= (df["Stopa Dywidendy (%)"].isna() | df["Stopa Dywidendy (%)"].between(div_min, div_max))
    if roe_wl: mask &= (df["ROE (%)"].isna() | df["ROE (%)"].between(roe_min, roe_max))
    if debt_wl: mask &= (df["Zadłużenie/Kapitał (%)"].isna() | df["Zadłużenie/Kapitał (%)"].between(debt_min, debt_max))
    if margin_wl: mask &= (df["Marża Zysku (%)"].isna() | df["Marża Zysku (%)"].between(margin_min, margin_max))

    filtered_df = df[mask]
    
    st.markdown("---")
    st.success(f"Znaleziono {len(filtered_df)} spółek spełniających wybrane kryteria (z {len(df)})")
    
    docelowe_kolumny = ["Spółka", "ISIN", "Rynek", "Cena", "P/E", "CAPE_Obliczone", "P/S", "P/BV", "Stopa Dywidendy (%)", "ROE (%)", "Zadłużenie/Kapitał (%)", "Marża Zysku (%)", "F-Score"]
    istniejace_kolumny = [kol for kol in docelowe_kolumny if kol in filtered_df.columns]
    
    widok_df = filtered_df[istniejace_kolumny].round(2)
    st.dataframe(widok_df, use_container_width=True, hide_index=True)
