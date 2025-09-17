import pandas as pd
import tqdm
import numpy as np
import re
import matplotlib.pyplot as plt

def extract_number(data):
    if not isinstance(data, str):
        return data

    raw = data.strip()
    text = raw.lower().replace(',', '.')
    
    # Correcciones comunes
    text = text.replace("o", "0")  # 2o -> 20, 6O -> 60
    text = re.sub(r"[^\d\.]+", " ", text)  # dejar solo números y puntos
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" .", ".").replace(". ", ".").strip("-")

    # Diccionario de equivalencias sin número
    equivalencias_sin_num = {
        "kg": 1000,
        "kilo": 1000,
        "kilos": 1000,
        "sobre": 30,
        "sachet": 30,
        "capsula": 0.5,
        "cápsula": 0.5,
        "capsula blanda": 1,
        "cápsula blanda": 1,
        "tableta": 1,
        "comprimido": 1,
        "pastilla": 1,
        "cucharada": 15,
        "cuchara": 15,
        "cuchara sopera": 15,
        "cucharadita": 5,
        "taza": 200,
        "barra": 40,
        "gota": 0.05,
    }

    # 1) Números explícitos con unidad (ej: "250 ml", "140 g")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|kg|ml)", raw.lower())
    if match:
        val = float(match.group(1))
        unidad = match.group(2)
        factores = {"mg": 0.001, "g": 1, "kg": 1000, "ml": 1}
        return val * factores.get(unidad, 1)

    # 2) Número aislado en el texto
    match = re.search(r"(\d+(?:\.\d+)?)", raw)
    if match:
        return float(match.group(1))

    # 3) Palabra clave sin número
    for k, v in equivalencias_sin_num.items():
        if k in raw.lower():
            return v

    # 4) Casos vacíos o inválidos
    if raw in [".", "-", "--", "por", "Por", ""]:
        return np.nan
    
    if raw == "0":
        return 0.0

    return np.nan




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
dfs = pd.read_excel("Catamarca.xls")  # force all cells as strings
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

productos = {}

total_cal = 0

others = []

for index, row in tqdm.tqdm(df.iterrows(), total=df.shape[0]):
    if row['RNPA'] in productos:
        continue
    productos[row['RNPA']] = {}
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

    total_cal += 1 if not np.isnan(calorias) and calorias > 0 else 0

    cal_o = not np.isnan(calorias) and calorias > 0

    ex_azucar = cal_o and not test_azucar(azucar, calorias)
    ex_grasas_totales = cal_o and not test_grasas_totales(grasas_totales, calorias)
    ex_grasas_saturadas = cal_o and not test_grasas_saturadas(grasas_saturadas, calorias)
    ex_sodio = (cal_o and not test_sodio_calorias(sodio, calorias)) or (not np.isnan(porcion) and porcion != 0 and not test_sodio_porcion(sodio, porcion))
    ex_calorias = cal_o and not np.isnan(porcion) and porcion != 0 and not test_calorias(calorias, porcion)

    if ex_azucar:
        excesos['Azucar'] += 1
    if ex_grasas_totales:
        excesos['Grasas Totales'] += 1
    if ex_grasas_saturadas:
        excesos['Grasas Saturadas'] += 1
    if ex_sodio:
        excesos['Sodio'] += 1
    if ex_calorias:
        excesos['Calorias'] += 1

    if (np.isnan(porcion) or porcion == 0) and row['Porcion'] != "nan":
        others.append(row['Porcion'])

    productos[row['RNPA']] = {
        'Azucar': (azucar, ex_azucar),
        'Calorias': (calorias, ex_calorias),
        'Grasas Totales': (grasas_totales, ex_grasas_totales),
        'Grasas Saturadas': (grasas_saturadas, ex_grasas_saturadas),
        'Sodio': (sodio, ex_sodio),
        'Porcion': porcion,
        'Ingrediente': row['INGREDIENTE'],
        "Categoria": row['CATEGORIA DE PRODUCTO']
    }
        

total = len(productos)
print(f"Total: {total}")
print()

print("Excesos absolutos:")
for key in excesos:
    print(f"{key}: {excesos[key]*100/total:.2f}%")

print()
print("Excesos relativos (solo productos con calorias):")
for key in excesos:
    print(f"{key}: {excesos[key]*100/total_cal:.2f}%")

print()
print("Otros (porciones no numericas):")
for other in set(others):
    print(f"- {other}")

# Graficar los resultados
labels = list(excesos.keys())
values = [excesos[key]*100/total for key in labels]

plt.figure()
plt.bar(labels, values)
plt.xlabel("Nutriente")
plt.ylabel("Porcentaje de Exceso")
plt.title("Exceso de Nutrientes en Productos Alimenticios")
plt.xticks(rotation=45)
plt.tight_layout()

plt.figure()
values2 = [excesos[key]*100/total_cal for key in labels]
plt.bar(labels, values2, color='orange')
plt.xlabel("Nutriente")
plt.ylabel("Porcentaje de Exceso (con calorias)")
plt.title("Exceso de Nutrientes en Productos Alimenticios (con calorias)")
plt.xticks(rotation=45)
plt.tight_layout()

sellos = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
for p in productos:
    ex_count = sum([1 for key in ['Azucar', 'Calorias', 'Grasas Totales', 'Grasas Saturadas', 'Sodio'] if productos[p][key][1]])
    sellos[ex_count] += 1

plt.figure()
plt.bar(sellos.keys(), [sellos[k]*100/total for k in sellos])
plt.xlabel("Cantidad de Sellos")
plt.ylabel("Porcentaje de Productos")
plt.title("Distribución de Cantidad de Sellos en Productos Alimenticios")
plt.xticks(list(sellos.keys()))
plt.tight_layout()


sellos = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
for p in productos:
    if productos[p]['Calorias'][0] > 0:
        ex_count = sum([1 for key in ['Azucar', 'Calorias', 'Grasas Totales', 'Grasas Saturadas', 'Sodio'] if productos[p][key][1]])
        sellos[ex_count] += 1
    
plt.figure()
plt.bar(sellos.keys(), [sellos[k]*100/total_cal for k in sellos])
plt.xlabel("Cantidad de Sellos")
plt.ylabel("Porcentaje de Productos")
plt.title("Distribución de Cantidad de Sellos en Productos Alimenticios")
plt.xticks(list(sellos.keys()))
plt.tight_layout()

# Print Categorias
plt.figure()
categorias = {}
for p in productos:
    cat = productos[p]['Categoria']
    if cat not in categorias:
        categorias[cat] = 0
    categorias[cat] += 1
plt.pie(categorias.values(), labels=categorias.keys(), autopct='%1.1f%%')



plt.show()
