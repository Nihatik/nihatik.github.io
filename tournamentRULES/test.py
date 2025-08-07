import sqlite3
import os
import re
from collections import defaultdict

conn = sqlite3.connect('pokemon.db')
cursor = conn.cursor()

cursor.execute("SELECT name, points, tier FROM streamcrafttiers WHERE points BETWEEN 0 AND 6")
db_regular = [(row[0], row[1], row[2], False) for row in cursor.fetchall()]

cursor.execute("SELECT name, pointsHa, tier FROM streamcrafttiers WHERE pointsHa BETWEEN 0 AND 6")
db_hidden = [(row[0], row[1], row[2], True) for row in cursor.fetchall()]

db_data = {}
for name, points, tier, is_hidden in db_regular + db_hidden:
    key = (name.strip().lower(), is_hidden)
    db_data[key] = (points, tier)

file_data_points = {} 

points_dir = 'points'
for point in range(1, 7):
    file_path = f'{point}.txt'
    path = os.path.join(points_dir, file_path)

    if not os.path.exists(path):
        print(f'Файл {path} не найден. Пропускаем.')
        continue

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            tier_match = re.search(r'\[(.*?)\]$', line)
            if tier_match:
                line = line[:tier_match.start()].strip()

            is_hidden = False
            hidden_match = re.match(r'^(.*?)(?:\s*)\(хид\)$', line, flags=re.IGNORECASE)
            if hidden_match:
                name = hidden_match.group(1).strip().lower()
                is_hidden = True
            else:
                name = line.strip().lower()

            file_data_points[(name, is_hidden)] = point

# --- Чтение данных TIER из директории tiers/ ---
tiers_dir = 'tiers'
file_data_tiers = {}  # (name, is_hidden) -> tier_name

if not os.path.exists(tiers_dir):
    print(f'Директория {tiers_dir} не найдена!')
else:
    for filename in os.listdir(tiers_dir):
        if not filename.endswith('.txt'):
            continue
        tier_name = os.path.splitext(filename)[0].strip()
        path = os.path.join(tiers_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                is_hidden = False
                hidden_match = re.match(r'^(.*?)(?:\s*)\(хид\)$', line, flags=re.IGNORECASE)
                if hidden_match:
                    name = hidden_match.group(1).strip().lower()
                    is_hidden = True
                else:
                    name = line.strip().lower()
                file_data_tiers[(name, is_hidden)] = tier_name


wrong_points = defaultdict(list)
wrong_tiers = defaultdict(list)
not_found_in_file_points = []
not_found_in_file_tiers = []
not_found_in_db_points = []
not_found_in_db_tiers = []

# Точка сравнения из БД с файлами
for key, (db_point, db_tier) in db_data.items():
    if key in file_data_points:
        file_point = file_data_points[key]
        if str(db_point) != str(file_point):
            wrong_points[(db_point, file_point)].append(f"{key[0]}{' (хид)' if key[1] else ''}")
    else:
        not_found_in_file_points.append(f"{key[0]}{' (хид)' if key[1] else ''}")

    if key in file_data_tiers:
        file_tier = file_data_tiers[key]
        if str(db_tier).strip().upper() != str(file_tier).strip().upper():
            wrong_tiers[(db_tier, file_tier)].append(f"{key[0]}{' (хид)' if key[1] else ''}")
    else:
        not_found_in_file_tiers.append(f"{key[0]}{' (хид)' if key[1] else ''}")

for key in file_data_points.keys():
    if key not in db_data:
        not_found_in_db_points.append(f"{key[0]}{' (хид)' if key[1] else ''}")

for key in file_data_tiers.keys():
    if key not in db_data:
        not_found_in_db_tiers.append(f"{key[0]}{' (хид)' if key[1] else ''}")

points_output = []

if wrong_points:
    points_output.append('=== Несовпадения POINTS (БД -> Файл) ===\n')
    for (actual, expected), names in sorted(wrong_points.items()):
        points_output.append(f'{actual} -> {expected}')
        points_output.extend(sorted(names))
        points_output.append('')

if not_found_in_file_points:
    points_output.append('=== Покемоны есть в БД, но не найдены в файлах POINTS ===\n')
    points_output.extend(sorted(not_found_in_file_points))
    points_output.append('')

if not_found_in_db_points:
    points_output.append('=== Покемоны есть в файлах POINTS, но не найдены в БД ===\n')
    points_output.extend(sorted(not_found_in_db_points))
    points_output.append('')

tiers_output = []

if wrong_tiers:
    tiers_output.append('=== Несовпадения TIER (БД -> Файл) ===\n')
    for (actual, expected), names in sorted(wrong_tiers.items()):
        tiers_output.append(f'{actual or "-"} -> {expected or "-"}')
        tiers_output.extend(sorted(names))
        tiers_output.append('')

if not_found_in_file_tiers:
    tiers_output.append('=== Покемоны есть в БД, но не найдены в файлах TIER ===\n')
    tiers_output.extend(sorted(not_found_in_file_tiers))
    tiers_output.append('')

if not_found_in_db_tiers:
    tiers_output.append('=== Покемоны есть в файлах TIER, но не найдены в БД ===\n')
    tiers_output.extend(sorted(not_found_in_db_tiers))
    tiers_output.append('')

with open('pointsRules.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(points_output))

with open('tiersRules.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(tiers_output))



conn.close()



def export_pokemon_points_to_file(db_path='../pokedex/pokemon.db', output_file='newPoints.txt'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    regular = {}
    hidden = {}

    # Сбор обычных
    cursor.execute("""
        SELECT name, points FROM streamcrafttiers 
        WHERE points BETWEEN 1 AND 6
    """)
    for name, points in cursor.fetchall():
        regular[name.strip().lower()] = (name, points)

    # Сбор хидден
    cursor.execute("""
        SELECT name, pointsHa FROM streamcrafttiers 
        WHERE pointsHa BETWEEN 1 AND 6
    """)
    for name, pointsHa in cursor.fetchall():
        hidden[name.strip().lower()] = (name, pointsHa)

    combined = {}  # key: name_lower -> (output_name, points)

    # Объединяем
    for key in set(regular.keys()).union(hidden.keys()):
        reg = regular.get(key)
        hid = hidden.get(key)

        if reg and hid:
            if reg[1] == hid[1]:
                combined[key] = (reg[0], reg[1])
            else:
                combined[key] = (reg[0], reg[1])
                combined[f"{key}_hid"] = (f"{hid[0]} (H)", hid[1])
        elif reg:
            combined[key] = (reg[0], reg[1])
        elif hid:
            combined[f"{key}_hid"] = (f"{hid[0]} (H)", hid[1])

    # Убираем только те формы, которые:
    # 1. содержат "-"
    # 2. имеют ту же базу без "-" с такими же баллами
    final_entries = {}
    for key, (name, points) in combined.items():
        name_clean = name.split(" (")[0]
        base_name = name_clean.split('-')[0].lower()

        is_form = '-' in name_clean
        is_hidden = name.endswith('(H)')

        if is_form:
            # Пробуем найти базовую версию (не скрытую)
            base_key = base_name
            base_entry = combined.get(base_key)
            if base_entry:
                base_points = base_entry[1]
                if base_points == points:
                    continue  # форма дублирует по баллам базу — не добавляем

        final_entries[key] = (name, points)

    # Группировка по баллам
    grouped = {}
    for name_out, points in final_entries.values():
        grouped.setdefault(points, []).append(name_out)

    # Запись
    lines = []
    for point in sorted(grouped.keys(), reverse=True):
        suffix = "баллов" if point in [5, 6] else "балла"
        lines.append(f"{point} {suffix}")
        for name in sorted(grouped[point]):
            lines.append(name)
        lines.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

# Вызов
export_pokemon_points_to_file()
