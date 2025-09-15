import pandas as pd
import tqdm
import numpy as np

def extract_number(data):
    if type(data) == str:
        data = data.replace(',', '.')
        if data == '1 cuchara de sopa':
            data = '15'
        if data == 'cuchara de sopa':
            data = '15'
        data = data.replace('gr', '')
        data = data.replace('GR', '')
        data = data.replace('g', '')
        data = data.replace('G', '')
        data = data.strip()
        try:
            return float(data)
        except:
            return np.nan
    return data

def test_azucar(azucar, calorias):
    porcentaje = azucar*4*100/calorias
    return porcentaje < 10

def test_grasas_totales(grasas, calorias):
    porcentaje = grasas*9*100/calorias
    return porcentaje < 30

def test_grasas_saturadas(grasas, calorias):
    porcentaje = grasas*9*100/calorias
    return porcentaje < 10

def test_sodio_calorias(sodio, calorias):
    porcentaje1 = sodio/calorias
    return porcentaje1 < 1

def test_sodio_porcion(sodio, porcion):
    porcentaje2 = sodio * 100/porcion
    return porcentaje2 < 300

def test_calorias(calorias, porcion):
    porcentaje3 = calorias * 100/porcion
    return porcentaje3 < 275

# Step 1: read Excel normally
dfs = pd.read_excel("INAL.xls")  # force all cells as strings
df = dfs

# Step 2: force everything back to strings (so 3,6 is preserved)
df = df.astype(str)

excesos = {'Azucar': 0,
           'Grasas Totales': 0,
           'Grasas Saturadas': 0,
           'Sodio': 0,
           'Cafeina': 0,
           'Edulcorante': 0,
           'Calorias': 0}

seen = []

for index, row in tqdm.tqdm(df.iterrows(), total=df.shape[0]):
    if row['RNPA'] in seen:
        continue
    seen.append(row['RNPA'])
    azucar = extract_number(row['AZUCAR'])
    calorias = extract_number(row['VALOR ENERGETICO (kcal)'])
    grasas_totales = extract_number(row['GRASAS TOTALES'])
    grasas_saturadas = extract_number(row['GRASAS SATURADAS'])
    sodio = extract_number(row['SODIO (mg)'])
    porcion = extract_number(row['Porcion'])

    if 'edulcorante' in row['INGREDIENTE'].lower() or 'sucralosa' in row['INGREDIENTE'].lower() or 'aspartamo' in row['INGREDIENTE'].lower() or 'acesulfamo' in row['INGREDIENTE'].lower() or 'sacarina' in row['INGREDIENTE'].lower():
        excesos['Edulcorante'] += 1
    if 'cafeína' in row['INGREDIENTE'].lower() or 'cafeina' in row['INGREDIENTE'].lower():
        excesos['Cafeina'] += 1

    cal_o = not np.isnan(calorias) and calorias > 0
    if cal_o and not test_azucar(azucar, calorias):
        excesos['Azucar'] += 1
    if cal_o and not test_grasas_totales(grasas_totales, calorias):
        excesos['Grasas Totales'] += 1
    if cal_o and not test_grasas_saturadas(grasas_saturadas, calorias):
        excesos['Grasas Saturadas'] += 1
    if (cal_o and not test_sodio_calorias(sodio, calorias)) or (not np.isnan(porcion) and porcion != 0 and not test_sodio_porcion(sodio, porcion)):
        excesos['Sodio'] += 1
    if cal_o and not np.isnan(porcion) and porcion != 0 and not test_calorias(calorias, porcion):
        excesos['Calorias'] += 1

total = len(seen)
print(f"Total: {total}")

for key in excesos:
    print(f"{key}: {excesos[key]*100/total:.2f}%")
