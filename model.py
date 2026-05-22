import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import catboost
import optuna
import json


def categorize_floor(floor):
    if floor == 0: 
        return 'Parter'
    elif 1 <= floor <= 3: 
        return 'Niskie'
    elif 4 <= floor <= 8: 
        return 'Srednie'
    else: 
        return 'Wysokie'

pd.set_option('display.float_format', '{:.2f}'.format)
flats = pd.read_csv('flats.csv')

flats['Floor'] = flats['Floor'].replace('parter', 0)
flats['Floor'] = flats['Floor'].astype(int)
flats['Price_Per_m2'] =  (flats['Price'] / flats['Square_Footage']).round(2)
flats['Street'] = flats['Street'].fillna('Brak')

price_limit = flats['Price'].quantile(0.98)
sqm_limit = flats['Square_Footage'].quantile(0.98)
price_btm_limit = flats['Price'].quantile(0.02)
sqm_btm_limit = flats['Square_Footage'].quantile(0.02)
ppm2_limit = flats['Price_Per_m2'].quantile(0.98)
ppm2_btm_limit = flats['Price_Per_m2'].quantile(0.02)

flats_filtred = flats[(flats['Price'] <= price_limit) & (flats['Price'] >= price_btm_limit) & 
                      (flats['Square_Footage'] >= sqm_btm_limit) & (flats['Square_Footage'] <= sqm_limit) &
                      (flats['Price_Per_m2'] >= ppm2_btm_limit) & (flats['Price_Per_m2'] <= ppm2_limit)].copy()


balcony_keywords = [
    'balkon', 'balkonu', 'balkonem', 'balkony', 'balkonami', 'balkonowy', 
    'taras', 'tarasu', 'tarasem', 'tarasie', 'tarasy', 'tarasów', 'tarasami',
    'loggia', 'loggi', 'loggią', 'loggie', 'loggiami', 'loggiei',
    'balkon_komórka', 'balkon18m2', 'balkony_bez', 'balkony_budowa', 
    '42m²balkon', 'pokoje_loggia'
]

garage_keywords = [
    '2garaz', '2garaże', '2xgaraż', 'factory_garaż', 'garaz', 'garazu', 
    'garaż', 'garaż_', 'garażami', 'garaże', 'garażem', 'garażowa', 
    'garażowa_zobacz', 'garażowe', 'garażowy', 'garażowymi', 'garażową', 
    'garażu', 'komórka_garaż', 'otwarte_metro_garaż',
    '2mpostojowe', 'dwumiejscowym', 'iparking', 'parking', 'parkingi', 
    'parkingiem', 'parkingow', 'parkingowe', 'parkingowym', 'parkingowymi', 
    'postoj', 'postojem', 'postojo', 'postojowe', 'postojowym', 'postojowymi',
    'miejsc', 'miejsca', 'miejscami', 'miejsce', 'miejscem', 'miejscu'
]

garden_keywords = ["ogródek", "ogródkiem", "ogród", "ogrodem", "ogródki", "ogródkami", 
            "ogrody", "ogrodzie", "ogrodu", "ogródka", "ogrodami", "ogróde", "ogrodkiem", 
            "iogródek", "ogródekiem", "ogródu", "ogród60mkw", "ogrodem_hala", "do_remontu_z_ogródkiem_obustronne_do_negocjacji"]

metro_keywords = ['metro', 'metra', 'metrze', 'metrem','metroratusz', 'dolinkąmetro', 
    '_metro', 'otwarte_metro', 'metroart', 'wielkanocny_metro', 'otwarte_metro_garaż'
]


patterns_to_columns = {
    'is_ready': ['nowy', 'nowa', 'nowe', 'gotowe', 'pod klucz', 'wykończony', 'wykończone', 'do wprowadzenia', 'do wejścia', 'do zamieszkania'],
    'needs_renovation': ['do remontu', 'do odświeżenia', 'do wykończenia', 'do aranżacji', 'do własnej aranżacji'],
    'is_renovated': ['po remoncie', 'po generalnym remoncie', 'wyremontowane', 'odświeżone'],
    'is_developer_state': ['deweloperski', 'stan deweloperski'],
    'is_premium': ['wysoki standard', 'premium', 'idealny', 'idealnym', 'świetny', 'zadbany', 'zadbane']
}

warsaw_districts = [
    'Mokotów', 'Wola', 'Białołęka', 'Praga-Południe', 'Śródmieście', 
    'Ursus', 'Ursynów', 'Włochy', 'Bemowo', 'Wilanów', 'Ochota', 
    'Targówek', 'Bielany', 'Praga-Północ', 'Wawer', 'Żoliborz', 
    'Rembertów', 'Wesoła'
]

premium_keywords = [
    "apartament","premium","penthouse","luksusowy","luksus",
    "wysoki standard","ekskluzywny","prestiżowy",
    "prestiż","wyjątkowy","residence","rezydencja","vip"
]

districs_correct = {
    'Kabaty': 'Ursynów',
    'Skorosze': 'Ursus',
    'Stegny': 'Mokotów'
}

for col_name, patterns in patterns_to_columns.items():
  
    regex_pattern = '|'.join(patterns)
    
   
    flats_filtred[col_name] = flats_filtred['Name'].str.contains(
        regex_pattern, 
        case=False, 
        na=False, 
        regex=True
    ).astype(int)

polish_signs = str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ')
flats_filtred['District'] = flats_filtred['District'].replace(districs_correct)
flats_filtred = flats_filtred[flats_filtred['District'].isin(warsaw_districts)]

pattern_balcony = '|'.join(balcony_keywords)
pattern_garage = '|'.join(garage_keywords)
pattern_garden = '|'.join(garden_keywords)
pattern_metro = '|'.join(metro_keywords)
pattern_premium = '|'.join(premium_keywords)

flats_filtred['Has_Balcony'] = flats_filtred['Name'].str.contains(pattern_balcony,case=False,na=False).astype(int)
flats_filtred['Has_Garage'] = flats_filtred['Name'].str.contains(pattern_garage,case=False,na=False).astype(int)
flats_filtred['Has_Garden'] = flats_filtred['Name'].str.contains(pattern_garden,case=False,na=False).astype(int)
flats_filtred['Has_Metro'] = flats_filtred['Name'].str.contains(pattern_metro,case=False,na=False).astype(int)
flats_filtred['Is_Premium'] = flats_filtred['Name'].str.contains(pattern_premium,case=False,na=False).astype(int)
flats_filtred['Avg_Room_Size'] = flats_filtred['Square_Footage'] / flats_filtred['Rooms']
flats_filtred['Year_From_Name'] = flats_filtred['Name'].str.extract(r'(19\d{2}|20\d{2})').astype(float)
flats_filtred['Year_From_Name'] = flats_filtred['Year_From_Name'].fillna(0)


flats_filtred['Floor_Cat'] = flats_filtred['Floor'].apply(categorize_floor)

ui_data = {'districts':sorted(flats_filtred['District'].unique().tolist()),
           'estates': sorted(flats_filtred['Estate'].dropna().unique().tolist()),
           'streets': sorted(flats_filtred['Street'].unique().tolist())
            }

with open('ui_options.json', 'w', encoding='utf-8') as f:
    json.dump(ui_data, f, ensure_ascii=False, indent=4)

y = np.log1p(flats_filtred['Price_Per_m2'])
x = flats_filtred.drop(columns=['Name', 'Price', 'Price_Per_m2'])


cat_features = ['Estate','District','Floor_Cat','Street']
x_temp, x_test, y_temp, y_test = train_test_split(x,y,test_size = 0.2,random_state =42)
x_train, x_val, y_train, y_val = train_test_split(x_temp, y_temp, test_size=0.25, random_state=42)


def objective(trial):
    param= {
        'iterations': trial.suggest_int('iterations',500,2000),
        'depth': trial.suggest_int('depth',4,10),
        'learning_rate': trial.suggest_float('learning_rate',0.01,0.2, log=True),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg',1,10),
        'random_strength': trial.suggest_float('random_strength', 1e-9, 10, log=True),
        'border_count': trial.suggest_int('border_count', 32, 255),
        'cat_features': cat_features,
        'random_state': 42,
        'verbose': False
    }
    model = catboost.CatBoostRegressor(**param)

    model.fit(x_train, y_train,eval_set=[(x_val, y_val)],early_stopping_rounds=50)

    predictions = np.expm1(model.predict(x_val))    
    y_val_real = np.expm1(y_val)

    mae = mean_absolute_error(y_val_real, predictions)

    return mae

study = optuna.create_study(direction='minimize')

study.optimize(objective, n_trials=30)

print("--------------------------------------------------")
print(f"Najlepsze znalezione parametry: {study.best_params}")
print(f"Najlepsze uzyskane MAE podczas optymalizacji: {study.best_value:.2f}")
print("--------------------------------------------------")

best_params = study.best_params
best_params['cat_features'] = cat_features
best_params['random_state'] = 42

final_model = catboost.CatBoostRegressor(**best_params, verbose=100)
final_model.fit(x_train, y_train)

predictions_final = np.expm1(final_model.predict(x_test))
y_test_real_final = np.expm1(y_test)
pred_train_final = np.expm1(final_model.predict(x_train))
y_train_real_final = np.expm1(y_train)

mae_final = mean_absolute_error(y_test_real_final, predictions_final)
rmse_final = np.sqrt(mean_squared_error(y_test_real_final, predictions_final))
r2_final = r2_score(y_test_real_final, predictions_final)

print(f"Błąd na zbiorze treningowym (MAE): {mean_absolute_error(y_train_real_final, pred_train_final):.2f}")
print(f"Błąd na zbiorze testowym (MAE): {mae_final:.2f}")
print(f"Błąd średniokwadratowy (RMSE): {rmse_final:.2f}")
print(f"Współczynnik R^2: {r2_final:.4f}")

final_model.save_model('catboost_model.cbm')