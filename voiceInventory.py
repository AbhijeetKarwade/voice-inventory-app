import json
import pandas as pd
import os
import re
from unidecode import unidecode
from fuzzywuzzy import fuzz, process
from datetime import datetime
import time
import matplotlib.pyplot as plt
from pandas.plotting import table

entry = []
stop_session_flag = False
session_active = False

# Shares the status of active session
def active_session():
    global session_active
    global entry
    return json.dumps({'active': session_active, 'entry': entry})

# Clears entries of active session
def clear_entry():
    global entry
    entry = []
    return entry

# Clears the contents of a JSON file
def empty_jsonFile(file_name):
    try:
        with open(file_name, 'w') as file:
            file.write('[]')
        return {'message': f'The file {file_name} has been cleared.'}
    except Exception as e:
        print(f"Error clearing {file_name}: {e}")
        raise Exception(f"Error clearing {file_name}: {e}")

# Converts Excel to JSON
def excel_2JSON(file_name, output_file, *columns):
    try:
        xls = pd.ExcelFile(file_name)
    except FileNotFoundError:
        print(f"Error: The file '{file_name}' was not found.")
        raise FileNotFoundError(f"File '{file_name}' not found")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        raise Exception(f"Error loading Excel file: {e}")
    
    all_data = []
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            cols_present = df.columns.tolist()
            cols_to_read = [col for col in columns if col in cols_present]
            if cols_to_read:
                selected_df = df[cols_to_read].dropna(how='all')
                selected_df = selected_df[~(selected_df.map(lambda x: isinstance(x, str) and x.strip() == '').all(axis=1))]
                if selected_df.empty:
                    print(f"No data in columns {cols_to_read} after removing blank rows.")
                else:
                    selected_df = selected_df.map(lambda x: x.lower() if isinstance(x, str) else x)
                    all_data.extend(selected_df.to_dict(orient='records'))
            else:
                print(f"None of the specified columns {columns} found in sheet {sheet_name}.")
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
    
    try:
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
    
    if base_name in ['vendors.json', 'materials.json', 'units.json']:
        if not isinstance(existing_data, list):
            existing_data = []
        key = 'vendor' if base_name == 'vendors.json' else 'material' if base_name == 'materials.json' else 'unit'
        existing_values = {item[key] for item in existing_data if key in item}
        for item in renamed_data:
            if key in item and item[key] not in existing_values:
                existing_data.append(item)
                existing_values.add(item[key])
    else:
        existing_data.extend(renamed_data)
    
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=4)
    print(f"Excel data saved to {output_file}")

# Export inventory to different formats
def export_inventory(file_name, format_type):
    json_file = 'inventory.json'
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
        if not data:
            raise ValueError("No data to export")
        df = pd.DataFrame(data)
        output_file = file_name.split()[0]
        if format_type == 'csv':
            df.to_csv(f"{output_file}.csv", index=False)
            print(f"Exported to {output_file}.csv")
        elif format_type == 'excel':
            df.to_excel(f"{output_file}.xlsx", index=False)
            print(f"Exported to {output_file}.xlsx")
        elif format_type == 'pdf':
            fig, ax = plt.subplots(figsize=(12, len(df) * 0.5 + 1))
            ax.axis('off')
            tbl = table(ax, df, loc='center', cellLoc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1, 1.5)
            plt.savefig(f"{output_file}.pdf", bbox_inches='tight')
            plt.close()
            print(f"Exported to {output_file}.pdf")
        else:
            raise ValueError("Unsupported format. Use 'csv', 'excel', or 'pdf'.")
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        raise FileNotFoundError(f"{json_file} not found")
    except json.JSONDecodeError:
        print(f"Error: {json_file} contains invalid JSON")
        raise ValueError(f"{json_file} contains invalid JSON")
    except Exception as e:
        print(f"Export error: {e}")
        raise Exception(f"Export error: {e}")

# Deletes entry from inventory.json
def delete_entry(entry2delete):
    json_file = 'inventory.json'
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
        entry2delete = json.loads(entry2delete.lower())
        new_inventory = [inv for inv in data if inv != entry2delete]
        with open(json_file, 'w') as f:
            json.dump(new_inventory, f, indent=4)
        print(f"Entry deleted from {json_file}")
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        raise FileNotFoundError(f"{json_file} not found")
    except json.JSONDecodeError:
        print(f"Error: {json_file} contains invalid JSON")
        raise ValueError(f"{json_file} contains invalid JSON")

# Speak function (client-side handles actual speech)
def speak(text):
    print(f"Speak: {text}")

# Saves record to inventory.json
def save_2json(sessionType, data, filename="inventory.json"):
    filepath = os.path.abspath(filename)
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
    try:
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
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")
        raise Exception(f"Error saving to {filepath}: {e}")

# Beep functions (client-side handles actual audio)
def play_beep(frequency=1000, duration=200):
    print(f"Beep: frequency={frequency}, duration={duration}")

def beep_prompt_supplier():
    print("Supplier prompt beep")

def beep_prompt_item():
    print("Item prompt beep")

def beep_prompt_quantity():
    print("Quantity prompt beep")

def beep_invalid_input():
    print("Invalid input beep")

def beep_item_added():
    print("Item added beep")
    time.sleep(0.1)
    print("Item added beep (second)")

# Extracts item and quantity from text
def get_item_quantity(text):
    text = unidecode(text.lower())
    pattern = r'([a-zA-Z0-9\s\.\*x+]+?)(?:quantity\s*|qnty\s*|qty\s*)(\d+)(?=\s*[a-zA-Z0-9\s\.\*x+]*?(?:quantity\s*|qnty\s*|qty\s*)|$|\s*$)'
    matches = re.findall(pattern, text)
    return [(match[0].strip(), int(match[1])) for match in matches] if matches else None

# Matches text with vendors, materials, or units
def match_text(match_type, input_text, df_type, threshold=60):
    try:
        cleaned_input = re.sub(r'[^a-zA-Z0-9\s+.]', '', unidecode(input_text.strip().lower())).replace("  ", " ")
        best_match = process.extractOne(cleaned_input, df_type["Cleaned_Name"], scorer=fuzz.token_sort_ratio)
        if best_match and best_match[1] >= threshold:
            key = 'vendor' if match_type == 'vendors' else 'material' if match_type == 'materials' else 'unit'
            return df_type[df_type["Cleaned_Name"] == best_match[0]].iloc[0][key]
        return None
    except Exception as e:
        print(f"Error matching {match_type}: {e}")
        return None

# Loads JSON file into DataFrame
def load_json(file_name):
    base_name = os.path.basename(file_name).lower()
    try:
        with open(file_name, mode="r", encoding='utf-8') as file:
            json_data = json.load(file)
        if not isinstance(json_data, list):
            raise ValueError(f"JSON file {file_name} must contain a list")
        df = pd.DataFrame(json_data)
        if base_name == 'vendors.json':
            if "vendor" not in df.columns:
                raise ValueError("JSON file must contain 'vendor' column")
            df = df.dropna(subset=["vendor"])
            df["Cleaned_Name"] = df["vendor"].apply(lambda x: re.sub(r'[^a-zA-Z0-9\s+.]', '', unidecode(str(x).strip().lower())).replace("  ", " "))
        elif base_name == 'materials.json':
            if "material" not in df.columns:
                raise ValueError("JSON file must contain 'material' column")
            df = df.dropna(subset=["material"])
            df["Cleaned_Name"] = df["material"].apply(lambda x: re.sub(r'[^a-zA-Z0-9\s+x+.]', '', unidecode(str(x).strip().lower())).replace("  ", " "))
        elif base_name == 'units.json':
            if "unit" not in df.columns:
                raise ValueError("JSON file must contain 'unit' column")
            df = df.dropna(subset=["unit"])
            df["Cleaned_Name"] = df["unit"].apply(lambda x: re.sub(r'[^a-zA-Z0-9\s+x+.]', '', unidecode(str(x).strip().lower())).replace("  ", " "))
        else:
            raise ValueError(f"Unsupported file: {file_name}. Expected 'vendors.json', 'materials.json', or 'units.json'")
        return df
    except FileNotFoundError:
        print(f"Error: {file_name} not found")
        raise FileNotFoundError(f"{file_name} not found")
    except json.JSONDecodeError:
        print(f"Error: {file_name} contains invalid JSON")
        raise ValueError(f"{file_name} contains invalid JSON")
    except Exception as e:
        print(f"Error loading {file_name}: {e}")
        raise Exception(f"Error loading {file_name}: {e}")

# Start inventory session
def start_inventory(sessionType):
    try:
        print(f"Starting {sessionType} session")
        df_vendors = load_json("vendors.json")
        print(f"✅ Loaded {len(df_vendors)} vendors")
        df_items = load_json("materials.json")
        print(f"✅ Loaded {len(df_items)} materials")
        df_units = load_json("units.json")
        print(f"✅ Loaded {len(df_units)} units")
        return f"Started {sessionType} entry"
    except Exception as e:
        print(f"Error starting {sessionType} session: {e}")
        raise Exception(f"Error starting session: {e}")

# Process session (client-side handles logic)
def process_session(sessionType, df_vendors, df_items, df_units):
    print(f"Processing {sessionType} session")

# Stop inventory session
def stop_inventory(sessionType):
    global stop_session_flag
    stop_session_flag = True
    print(f"Stopped {sessionType} session")
    return f"Stopped {sessionType} entry"

# Start session endpoint
def start_session(sessionType):
    global session_active
    session_active = True
    return start_inventory(sessionType)

# Stop session endpoint
def stop_session(sessionType):
    global session_active
    session_active = False
    return stop_inventory(sessionType)