import json
import pandas as pd
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
from pandas.plotting import table
import pyttsx3
from datetime import datetime
import re
from unidecode import unidecode
from fuzzywuzzy import fuzz, process
import speech_recognition as sr
import os
import time
import platform

entry = []
stop_session_flag = False
session_active = False

DATA_DIR = os.getenv('DATA_DIR', os.getcwd())  # Default to current directory if not set

def active_session():
    global session_active
    global entry
    if entry:
        print(entry[0])
        dt = datetime.strptime(entry[0][0], "%Y-%m-%d %H:%M:%S")
    return json.dumps({'active': session_active, 'entry': entry})

def clear_entry():
    global entry
    entry = []
    return entry

def load_data():
    with open(os.path.join(DATA_DIR, 'vendors.json')) as vendors_file:
        vendors = json.load(vendors_file)
    with open(os.path.join(DATA_DIR, 'materials.json')) as materials_file:
        materials = json.load(materials_file)
    with open(os.path.join(DATA_DIR, 'units.json')) as units_file:
        units = json.load(units_file)
    return vendors, materials, units

def get_data():
    vendors, materials, units = load_data()
    return json.dumps({'vendors': vendors, 'materials': materials, 'units': units})

def get_vendors():
    with open(os.path.join(DATA_DIR, 'vendors.json')) as vendors_file:
        vendors = json.load(vendors_file)
    return json.dumps({'vendors': vendors})

def get_materials():
    with open(os.path.join(DATA_DIR, 'materials.json')) as materials_file:
        materials = json.load(materials_file)
    return json.dumps({'materials': materials})

def get_units():
    with open(os.path.join(DATA_DIR, 'units.json')) as units_file:
        units = json.load(units_file)
    return json.dumps({'units': units})

def add_vendor(new_vendor):
    vendors_data = get_vendors()
    vendors = json.loads(vendors_data)
    for vendor in vendors['vendors']:
        if vendor['vendor'] == new_vendor:
            return json.dumps({'message': 'Vendor already exists!'})
    vendors['vendors'].append({'vendor': new_vendor})
    with open(os.path.join(DATA_DIR, 'vendors.json'), 'w') as vendors_file:
        json.dump(vendors['vendors'], vendors_file)
    return json.dumps({'message': 'Vendor added successfully!'})

def add_material(new_material):
    materials_data = get_materials()
    materials = json.loads(materials_data)
    for material in materials['materials']:
        if material['material'] == new_material:
            return json.dumps({'message': 'Material already exists!'})
    materials['materials'].append({'material': new_material})
    with open(os.path.join(DATA_DIR, 'materials.json'), 'w') as materials_file:
        json.dump(materials['materials'], materials_file)
    return json.dumps({'message': 'Material added successfully!'})

def add_materialUnit(new_material, new_unit):
    unitsFlag = False
    materials_data = get_materials()
    materials = json.loads(materials_data)
    units_data = get_units()
    units = json.loads(units_data)
    for material in materials['materials']:
        if material['material'] == new_material:
            return json.dumps({'message': 'Material already exists!'})
    for unit in units['units']:
        if unit['unit'] == new_unit:
            unitsFlag = True
            break
        else:
            unitsFlag = False
    materials['materials'].append({'material': new_material, 'unit': new_unit})
    with open(os.path.join(DATA_DIR, 'materials.json'), 'w') as materials_file:
        json.dump(materials['materials'], materials_file)
    if not unitsFlag:
        units['units'].append({'unit': new_unit})
        with open(os.path.join(DATA_DIR, 'units.json'), 'w') as units_file:
            json.dump(units['units'], units_file)
    return json.dumps({'message': 'Material added successfully!'})

def add_unit(new_unit):
    units_data = get_units()
    units = json.loads(units_data)
    for unit in units['units']:
        if unit['unit'] == new_unit:
            return json.dumps({'message': 'Unit already exists!'})
    units['units'].append({'unit': new_unit})
    with open(os.path.join(DATA_DIR, 'units.json'), 'w') as units_file:
        json.dump(units['units'], units_file)
    return json.dumps({'message': 'Unit added successfully!'})

def delete_vendor(vendor_to_delete):
    vendors_data = get_vendors()
    vendors = json.loads(vendors_data)
    for vendor in vendors['vendors']:
        if vendor['vendor'] == vendor_to_delete:
            vendors['vendors'] = [u for u in vendors['vendors'] if u['vendor'] != vendor_to_delete]
            with open(os.path.join(DATA_DIR, 'vendors.json'), 'w') as vendors_file:
                json.dump(vendors['vendors'], vendors_file)
            return json.dumps({'message': 'Vendor deleted successfully!'})
    return json.dumps({'message': 'Vendor not found!'})

def delete_material(material_to_delete):
    materials_data = get_materials()
    materials = json.loads(materials_data)
    for material in materials['materials']:
        if material['material'] == material_to_delete:
            materials['materials'] = [u for u in materials['materials'] if u['material'] != material_to_delete]
            with open(os.path.join(DATA_DIR, 'materials.json'), 'w') as materials_file:
                json.dump(materials['materials'], materials_file)
            return json.dumps({'message': 'Material deleted successfully!'})
    return json.dumps({'message': 'Material not found!'})

def delete_unit(unit_to_delete):
    units_data = get_units()
    units = json.loads(units_data)
    for unit in units['units']:
        if unit['unit'] == unit_to_delete:
            units['units'] = [u for u in units['units'] if u['unit'] != unit_to_delete]
            with open(os.path.join(DATA_DIR, 'units.json'), 'w') as units_file:
                json.dump(units['units'], units_file)
            return json.dumps({'message': 'Unit deleted successfully!'})
    return json.dumps({'message': 'Unit not found!'})

def retrieve_inventory():
    json_file = os.path.join(DATA_DIR, 'inventory.json')
    try:
        with open(json_file, 'r') as file:
            data = file.read()
        return data
    except FileNotFoundError:
        print(f"Error: The file {json_file} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file {json_file} is not a valid JSON file.")
        return None

def delete_entry(entry2delete):
    json_file = os.path.join(DATA_DIR, 'inventory.json')
    try:
        with open(json_file, 'r') as file:
            data = file.read()
        data = json.loads(data.lower())
        entry2delete = json.loads(entry2delete.lower())
        new_inventory = [inv for inv in data if inv != entry2delete]
        with open(json_file, 'w') as f:
            json.dump(new_inventory, f, indent=4)
    except FileNotFoundError:
        print(f"Error: The file {json_file} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file {json_file} is not a valid JSON file.")
        return None

def export_inventory(file_name, format_type):
    json_file = os.path.join(DATA_DIR, 'inventory.json')
    output_file = file_name.split()
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
        print(data)
        if format_type == 'csv':
            df = pd.DataFrame(data)
            df.to_csv(os.path.join(DATA_DIR, output_file[0] + ".csv"), index=False)
            print(f"Data has been converted to CSV and saved as {output_file[0]}")
        elif format_type == 'excel':
            df = pd.DataFrame(data)
            df.to_excel(os.path.join(DATA_DIR, output_file[0] + '.xlsx'), index=False)
            print(f"Data has been converted to Excel and saved as {output_file[0]}")
        elif format_type == 'pdf':
            df = pd.DataFrame(data)
            fig, ax = plt.subplots(figsize=(12, len(df) * 0.5 + 1))
            ax.axis('off')
            tbl = table(ax, df, loc='center', cellLoc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1, 1.5)
            plt.savefig(os.path.join(DATA_DIR, output_file[0] + '.pdf'), bbox_inches='tight')
            plt.close()
            print(f"Data has been converted to PDF and saved as {output_file[0]}")
        else:
            print("Unsupported format type. Please choose 'csv', 'excel', or 'pdf'.")
    except json.JSONDecodeError:
        print(f"Error: The file {json_file} contains invalid JSON.")
    except FileNotFoundError:
        print(f"Error: The file {json_file} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def empty_jsonFile(file_name):
    try:
        with open(os.path.join(DATA_DIR, file_name), 'w') as file:
            file.write('[]')
        return json.dumps({'message': f'The file {file_name} has been cleared.'})
    except Exception as e:
        print(f"An error occurred while clearing the file {file_name}: {e}")
        return json.dumps({'message': f'An error occurred while clearing the file {file_name}: {e}'})

def excel_2JSON(file_name, output_file, *columns):
    try:
        xls = pd.ExcelFile(file_name)
    except FileNotFoundError:
        print(f"Error: The file '{file_name}' was not found.")
        return
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return
    
    all_data = []
    for sheet_name in xls.sheet_names:
        print(f"Sheet: {sheet_name}")
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            cols_present = df.columns.tolist()
            cols_to_read = [col for col in columns if col in cols_present]
            if cols_to_read:
                selected_df = df[cols_to_read].dropna(how='all')
                selected_df = selected_df[~(selected_df.map(lambda x: isinstance(x, str) and x.strip() == '').all(axis=1))]
                if selected_df.empty:
                    print(f"No data found in columns {cols_to_read} after removing blank rows.")
                else:
                    selected_df = selected_df.map(lambda x: x.lower() if isinstance(x, str) else x)
                    all_data.extend(selected_df.to_dict(orient='records'))
            else:
                print(f"None of the specified columns {columns} found in this sheet.")
        except Exception as e:
            print(f"Error processing sheet '{sheet_name}': {e}")
    
    xls.close()
    base_name = os.path.basename(output_file).lower()
    if base_name == 'vendors.json':
        key_mapping = {columns[0]: 'vendor'}
    elif base_name == 'materials.json':
        key_mapping = {columns[0]: 'material'}
    elif base_name == 'units.json':
        key_mapping = {columns[0]: 'unit'}
    else:
        key_mapping = {col: col for col in columns}
    
    renamed_data = []
    for item in all_data:
        new_item = {}
        for orig_key, new_key in key_mapping.items():
            if orig_key in item:
                new_item[new_key] = item[orig_key]
        if new_item:
            renamed_data.append(new_item)
    
    print(f"Collected data: {renamed_data}")
    try:
        with open(os.path.join(DATA_DIR, output_file), 'r') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
    
    if base_name == 'vendors.json':
        if not isinstance(existing_data, list):
            existing_data = []
        for item in renamed_data:
            if 'vendor' in item:
                if not any(d['vendor'] == item['vendor'] for d in existing_data):
                    existing_data.append(item)
    elif base_name == 'materials.json':
        if not isinstance(existing_data, list):
            existing_data = []
        for item in renamed_data:
            if 'material' in item:
                if not any(d['material'] == item['material'] for d in existing_data):
                    existing_data.append(item)
    elif base_name == 'units.json':
        if not isinstance(existing_data, list):
            existing_data = []
        for item in renamed_data:
            if 'unit' in item:
                if not any(d['unit'] == item['unit'] for d in existing_data):
                    existing_data.append(item)
    else:
        if not isinstance(existing_data, list):
            existing_data = []
        existing_data.extend(renamed_data)
    
    if base_name == 'vendors.json':
        unique_data = []
        seen_vendors = set()
        for item in existing_data:
            if 'vendor' in item and item['vendor'] not in seen_vendors:
                seen_vendors.add(item['vendor'])
                unique_data.append(item)
        existing_data = unique_data
    elif base_name == 'materials.json':
        unique_data = []
        seen_pairs = set()
        for item in existing_data:
            if 'material' in item:
                pair = item['material']
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    unique_data.append(item)
        existing_data = unique_data
    elif base_name == 'units.json':
        unique_data = []
        seen_pairs = set()
        for item in existing_data:
            if 'unit' in item:
                pair = item['unit']
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    unique_data.append(item)
        existing_data = unique_data
    
    with open(os.path.join(DATA_DIR, output_file), 'w') as f:
        json.dump(existing_data, f, indent=4)

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    print(text)
    engine.say(text)
    engine.runAndWait()

def save_2json(sessionType, data, filename="inventory.json"):
    filepath = os.path.join(DATA_DIR, filename)
    json_data = [
        {
            "Date": item[0],
            "Vendor": item[1],
            "Item": item[2],
            "Quantity": item[3],
            "Unit": item[4],
            "Session": sessionType
        } for item in data
    ]
    if os.path.exists(filepath):
        with open(filepath, mode="r", encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
        json_data = existing_data + json_data
    with open(filepath, mode="w", encoding='utf-8') as file:
        json.dump(json_data, file, indent=4)
    print(f"✅ Saved to: {filepath}")

def play_beep(frequency=1000, duration=200):
    if platform.system() == "Windows":
        import winsound
        winsound.Beep(frequency, duration)
    else:
        try:
            os.system(f"beep -f {frequency} -l {duration}")
        except:
            print("\a")

def beep_prompt_supplier():
    play_beep(frequency=800, duration=200)

def beep_prompt_item():
    play_beep(frequency=800, duration=200)

def beep_prompt_quantity():
    play_beep(frequency=800, duration=200)

def beep_invalid_input():
    play_beep(frequency=3000, duration=800)

def beep_item_added():
    play_beep(frequency=1200, duration=200)
    time.sleep(0.1)
    play_beep(frequency=1200, duration=200)

def match_item(item_name, df_items, threshold=70):
    cleaned_input = re.sub(r'[^a-zA-Z0-9\s+.]', '', unidecode(item_name.strip().lower())).replace("  ", " ")
    best_match = process.extractOne(cleaned_input, df_items["Cleaned_Name"], scorer=fuzz.token_sort_ratio)
    if best_match and best_match[1] >= threshold:
        row = df_items[df_items["Cleaned_Name"] == best_match[0]].iloc[0]
        return row["material"], row["unit"]
    return None, None

def get_item_quantity(text):
    text = unidecode(text.lower())
    pattern = r'([a-zA-Z0-9\s\.\*x+]+?)(?:quantity\s*|qnty\s*|qty\s*)(\d+)(?=\s*[a-zA-Z0-9\s\.\*x+]*?(?:quantity\s*|qnty\s*|qty\s*)|$|\s*$)'
    matches = re.findall(pattern, text)
    return [(match[0].strip(), int(match[1])) for match in matches] if matches else None

def match_vendor(vendor_name, df_vendors, threshold=70):
    cleaned_input = re.sub(r'[^a-zA-Z0-9\s+.]', '', unidecode(vendor_name.strip().lower())).replace("  ", " ")
    best_match = process.extractOne(cleaned_input, df_vendors["Cleaned_Name"], scorer=fuzz.token_sort_ratio)
    return df_vendors[df_vendors["Cleaned_Name"] == best_match[0]].iloc[0]["vendor"] if best_match and best_match[1] >= threshold else None

def match_text(match_type, input_text, df_type, threshold=60):
    cleaned_input = re.sub(r'[^a-zA-Z0-9\s+.]', '', unidecode(input_text.strip().lower())).replace("  ", " ")
    best_match = process.extractOne(cleaned_input, df_type["Cleaned_Name"], scorer=fuzz.token_sort_ratio)
    if match_type == 'vendors':
        return df_type[df_type["Cleaned_Name"] == best_match[0]].iloc[0]["vendor"] if best_match and best_match[1] >= threshold else None
    elif match_type == 'materials':
        return df_type[df_type["Cleaned_Name"] == best_match[0]].iloc[0]["material"] if best_match and best_match[1] >= threshold else None
    elif match_type == 'units':
        return df_type[df_type["Cleaned_Name"] == best_match[0]].iloc[0]["unit"] if best_match and best_match[1] >= threshold else None

def audio_2text():
    global stop_session_flag
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        if stop_session_flag:
            stop_session_flag = False
            speak("Session completed.")
            return
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="en-IN").lower()
            print(f"✅ You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏳ No speech detected, listening again...")
        except sr.UnknownValueError:
            print("I could not understand. Please try again.")
        except (sr.RequestError, ConnectionAbortedError, Exception) as e:
            print(f"Error: {str(e)}")
            return None

def process_session(sessionType, df_vendors, df_items, df_units):
    global entry
    global stop_session_flag
    global session_active
    entry = []
    count = 0
    while True:
        if stop_session_flag:
            stop_session_flag = False
            speak("Session completed.")
            return
        beep_prompt_supplier()
        print('----1----')
        input_text = audio_2text()
        if input_text in ["stop", "exit", "done", "close"]:
            session_active = False
            speak("Session completed.")
            return
        if not input_text or not (matched_text := match_text('vendors', input_text, df_vendors)):
            play_beep(frequency=2500, duration=800)
            count = count + 1
            if count > 4:
                session_active = False
                count = 0
                print("Exit...")
                return
            continue
        else:
            play_beep(frequency=1000, duration=200)
            vendor = matched_text
            break
    while vendor:
        if stop_session_flag:
            stop_session_flag = False
            speak("Session completed.")
            return
        print('----2----')
        beep_prompt_item()
        input_text = audio_2text()
        if input_text in ["stop", "exit", "done", "close"]:
            session_active = False
            speak("Session completed.")
            return
        if not input_text:
            play_beep(frequency=2500, duration=800)
            count = count + 1
            if count > 4:
                session_active = False
                count = 0
                return
            continue
        material = match_text('materials', input_text, df_items)
        if not material:
            play_beep(frequency=2500, duration=800)
            count = count + 1
            if count > 4:
                session_active = False
                count = 0
                return
            continue
        else:
            play_beep(frequency=1000, duration=200)
        while material:
            if stop_session_flag:
                stop_session_flag = False
                speak("Session completed.")
                return
            print('----3----')
            beep_prompt_item()
            input_text = audio_2text()
            if input_text in ["stop", "exit", "done", "close"]:
                session_active = False
                speak("Session completed.")
                return
            if not input_text:
                play_beep(frequency=2500, duration=800)
                count = count + 1
                if count > 4:
                    session_active = False
                    count = 0
                    return
                continue
            else:
                text_split = input_text.split()
                quantity = re.findall(r'\d+', text_split[0])
                if len(text_split) > 1:
                    unit = match_text('units', text_split[1], df_units)
                else:
                    unit = 'undefined'
                if quantity:
                    try:
                        entry.append([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            vendor,
                            material,
                            quantity[0],
                            unit,
                            sessionType
                        ])
                        beep_item_added()
                        break
                    except ValueError:
                        beep_invalid_input()
                        continue

def load_json(file_name):
    base_name = os.path.basename(file_name).lower()
    with open(os.path.join(DATA_DIR, file_name), mode="r", encoding='utf-8') as file:
        json_data = json.load(file)
    if base_name == 'vendors.json':
        if isinstance(json_data, list):
            df = pd.DataFrame(json_data)
        else:
            if "vendors" not in json_data:
                raise ValueError("JSON file must contain a 'vendors' key")
            df = pd.DataFrame(json_data["vendors"])
        if "vendor" not in df.columns:
            raise ValueError("JSON file must contain 'vendor' column")
        df = df.dropna(subset=["vendor"])
        df["Cleaned_Name"] = df["vendor"].apply(lambda x:
            re.sub(r'[^a-zA-Z0-9\s+.]', '', unidecode(str(x).strip().lower())).replace("  ", " "))
        return df
    elif base_name == 'materials.json':
        df = pd.DataFrame(json_data)
        if "material" not in df.columns:
            raise ValueError("JSON file must contain 'material' column")
        df = df.dropna(subset=["material"])
        df["Cleaned_Name"] = df["material"].apply(lambda x:
            re.sub(r'[^a-zA-Z0-9\s+x+.]', '', unidecode(str(x).strip().lower())).replace("  ", " "))
        return df
    elif base_name == 'units.json':
        df = pd.DataFrame(json_data)
        if "unit" not in df.columns:
            raise ValueError("JSON file must contain 'unit' column")
        df = df.dropna(subset=["unit"])
        df["Cleaned_Name"] = df["unit"].apply(lambda x:
            re.sub(r'[^a-zA-Z0-9\s+x+.]', '', unidecode(str(x).strip().lower())).replace("  ", " "))
        return df
    else:
        raise ValueError(f"Unsupported file: {file_name}. Expected 'materials.json' or 'vendors.json' or units.json")

def start_inventory(sessionType):
    print("Loading vendor database...")
    df_vendors = load_json("vendors.json")
    print(f"✅ Loaded {len(df_vendors)} vendors")
    print("Loading product database...")
    df_items = load_json("materials.json")
    print(f"✅ Loaded {len(df_items)} materials")
    print("Loading product database...")
    df_units = load_json("units.json")
    print(f"✅ Loaded {len(df_units)} units")
    speak("System ready")
    process_session(sessionType, df_vendors, df_items, df_units)

def stop_inventory(sessionType):
    print("Stop inventory session")
    global stop_session_flag
    stop_session_flag = True

def start_session(sessionType):
    if os.getenv('RENDER', 'false').lower() == 'true':
        return json.dumps({'message': 'Voice features are disabled on Render'})
    global session_active
    if sessionType == 'inward':
        session_active = True
        start_inventory('inward')
        return "Started inward entry"
    elif sessionType == 'outward':
        session_active = True
        start_inventory('outward')
        return 'Started outward entry'

def stop_session(sessionType):
    global session_active
    if sessionType == 'inward':
        session_active = False
        stop_inventory('inward')
        return "Stopped inward entry"
    elif sessionType == 'outward':
        session_active = False
        stop_inventory('outward')
        return 'Stopped outward entry'

def main():
    export_inventory('demo_output', 'pdf')

if __name__ == "__main__":
    main()