import streamlit as st
import json 
import pandas as pd
import numpy as np
import catboost

@st.cache_resource

def load_assets():
    model = catboost.CatBoostRegressor()
    model.load_model('catboost_model.cbm')


    with open('ui_options.json','r',encoding='utf-8') as file:
        ui_options = json.load(file)
    return model, ui_options

try:
    model, ui_options = load_assets()
except Exception as e:
    st.error(f"Nie udało się wczytać modelu lub pliku JSON. Upewnij się, że są w tym samym folderze. Błąd: {e}")
    st.stop()


st.set_page_config(page_title="Wycena mieszkań w Warszawie",layout="wide")

st.title("Kalkulator cen mieszkań w Warszawie")
st.write("Wprowadź parametry")


col1, col2 = st.columns(2)

with col1:
    st.header("Podstawowe informacje")
    square_footage = st.number_input("Powierzchnia (m^2)", min_value=10.0,max_value=200.0)
    rooms = st.number_input("Liczba pokoi", min_value=1, max_value=10, value=2)
    floor = st.number_input("Piętro",min_value=1,max_value=40, value = 2)
    year = st.number_input("Rok budowy (wpisz 0 jeśli nieznany)", min_value=0, max_value=2026, value=0)
with col2:
    st.header("Lokalizacja")
    district = st.selectbox("Dzielnica",ui_options['districts'])
    estate = st.selectbox("Osiedle",ui_options['estates'])
    street = st.selectbox("Ulica", ui_options['streets'])

st.write("---")
st.write("Cechy dodatkowe")

ch_col1, ch_col2 = st.columns(2)

with ch_col1:
    has_balcony = st.checkbox("Balkon / Taras / Loggia")
    has_garage = st.checkbox("Garaż / Miejsce postojowe / Parking")
    has_garden = st.checkbox("Ogródek")
    has_metro = st.checkbox("Blisko stacji metra")
    is_premium = st.checkbox("W tytule słowa Premium / Apartament / Luksusowy")

with ch_col2:
    is_ready = st.checkbox("Gotowe do wprowadzenia / Nowe / Pod klucz")
    needs_renovation = st.checkbox("Do remontu / odświeżenia")
    is_renovated = st.checkbox("Po generalnym remoncie / odświeżone")
    is_developer_state = st.checkbox("Stan deweloperski")
    is_premium_std = st.checkbox("Wysoki standard / Idealny stan")

st.write("---")

if st.button("Oblicz cenę mieszkania", type="primary"):
    avg_room_size = square_footage/rooms
    if floor == 0:
        floor_cat = 'Parter'
    elif 1 <= floor <= 3:
        floor_cat = 'Niskie'
    elif 4 <= floor <= 8:
        floor_cat = 'Srednie'
    else:
        floor_cat = 'Wysokie'

    input_data = {
        'Floor': floor,
        'Square_Footage': square_footage,
        'Rooms': rooms,
        'Street': street,
        'District': district,
        'Estate': estate,
        'is_ready': int(is_ready),
        'needs_renovation': int(needs_renovation),
        'is_renovated': int(is_renovated),
        'is_developer_state': int(is_developer_state),
        'is_premium': int(is_premium_std), 
        'Has_Balcony': int(has_balcony),
        'Has_Garage': int(has_garage),
        'Has_Garden': int(has_garden),
        'Has_Metro': int(has_metro),
        'Is_Premium': int(is_premium),
        'Avg_Room_Size': avg_room_size,
        'Year_From_Name': float(year),
        'Floor_Cat': floor_cat
    }

    input_df = pd.DataFrame([input_data])
    feature_order = model.feature_names_
    input_df = input_df[feature_order]

    predicted_log_price = model.predict(input_df)[0]
    predicted_price_per_m2 = np.expm1(predicted_log_price)
    
    total_price = predicted_price_per_m2 * square_footage

    st.header("Wynik estymacji modelu:")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(
            label="Szacowana całkowita cena mieszkania", 
            value=f"{total_price:,.2f} PLN".replace(",", " ")
        )
    with res_col2:
        st.metric(
            label="Średnia cena za metr kwadratowy", 
            value=f"{predicted_price_per_m2:,.2f} PLN/m²".replace(",", " ")
        )