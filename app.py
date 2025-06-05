from flask import Flask, jsonify, request, send_from_directory
import json
import os
import voiceInventory

from voiceInventory import excel_2JSON, start_session, stop_session, active_session, clear_entry, delete_entry
from voiceInventory import *

app = Flask(__name__)

DATA_DIR = os.getenv('DATA_DIR', os.getcwd())  # Default to current directory if not set

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'index.html')

# Load vendors, materials, and units from JSON files
def load_data():
    with open(os.path.join(DATA_DIR, 'vendors.json')) as vendors_file:
        vendors = json.load(vendors_file)
    with open(os.path.join(DATA_DIR, 'materials.json')) as materials_file:
        materials = json.load(materials_file)
    with open(os.path.join(DATA_DIR, 'units.json')) as units_file:
        units = json.load(units_file)
    return vendors, materials, units

# Endpoint to get vendors and materials
@app.route('/data', methods=['GET'])
def get_data():
    vendors, materials, units = load_data()
    return jsonify({'vendors': vendors, 'materials': materials, 'units': units})

# Endpoint to get vendors
@app.route('/get_vendors', methods=['GET'])
def get_vendors():
    with open(os.path.join(DATA_DIR, 'vendors.json')) as vendors_file:
        vendors = json.load(vendors_file)
    return jsonify({'vendors': vendors})

# Endpoint to get materials
@app.route('/get_materials', methods=['GET'])
def get_materials():
    with open(os.path.join(DATA_DIR, 'materials.json')) as materials_file:
        materials = json.load(materials_file)
        print(materials)
    return jsonify({'materials': materials})

# Endpoint to add a new vendor
@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    new_vendor = request.json.get('vendor')
    if new_vendor:
        vendors, materials, units = load_data()
        vendors.append({'vendor': new_vendor})
        with open(os.path.join(DATA_DIR, 'vendors.json'), 'w') as vendors_file:
            json.dump(vendors, vendors_file)
        return jsonify({'message': 'Vendor added successfully!'}), 201
    return jsonify({'error': 'Vendor name is required!'}), 400

# Endpoint to add a new material
@app.route('/add_material', methods=['POST'])
def add_material():
    new_material = request.json.get('material')
    new_unit = request.json.get('unit')
    print(new_material, new_unit)
    if new_material:
        vendors, materials, units = load_data()
        materials.append({'material': new_material})
        units.append({'unit': new_unit})
        with open(os.path.join(DATA_DIR, 'materials.json'), 'w') as materials_file:
            json.dump(materials, materials_file)
        with open(os.path.join(DATA_DIR, 'units.json'), 'w') as units_file:
            json.dump(units, units_file)
        return jsonify({'message': 'Material with unit added successfully!'}), 201
    return jsonify({'error': 'Material name is required!'}), 400

# Endpoint to delete a vendor
@app.route('/delete_vendor', methods=['POST'])
def delete_vendor():
    vendor_to_delete = request.json.get('vendor')
    if vendor_to_delete:
        vendors, materials, units = load_data()
        vendors = [vendor for vendor in vendors if vendor['vendor'] != vendor_to_delete]
        with open(os.path.join(DATA_DIR, 'vendors.json'), 'w') as vendors_file:
            json.dump(vendors, vendors_file)
        return jsonify({'success': True}), 200
    return jsonify({'success': False, 'message': 'Vendor not found!'}), 404

# Endpoint to delete a material
@app.route('/delete_material', methods=['POST'])
def delete_material():
    material_to_delete = request.json.get('material')
    if material_to_delete:
        vendors, materials, units = load_data()
        materials = [material for material in materials if material['material'] != material_to_delete]
        with open(os.path.join(DATA_DIR, 'materials.json'), 'w') as materials_file:
            json.dump(materials, materials_file)
        return jsonify({'success': True}), 200
    return jsonify({'success': False, 'message': 'Material not found!'}), 404

# Endpoint to import Excel file
@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided!'}), 400
    file = request.files['file']
    output_file = request.form.get('output_file')
    columns = request.form.get('columns').split(',')
    
    if not file or not output_file or not columns:
        return jsonify({'error': 'Missing file, output_file, or columns!'}), 400
    
    try:
        # Save the uploaded file temporarily
        temp_path = os.path.join(DATA_DIR, file.filename)
        file.save(temp_path)
        
        # Call excel_2JSON from voiceInventory
        voiceInventory.excel_2JSON(temp_path, os.path.join(DATA_DIR, output_file), *columns)
        
        # Remove the temporary file
        os.remove(temp_path)
        
        return jsonify({'message': f'Successfully converted {file.filename} to {output_file}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to save inventory
@app.route('/save_inventory', methods=['POST'])
def save_inventory():
    items = request.json.get('items')
    if not items:
        return jsonify({'error': 'No items provided!'}), 400
    try:
        formatted_items = [[
            item['date'],
            item['vendor'],
            item['item'],
            item['quantity'],
            item['unit'],
            item['session']
        ] for item in items]
        for item in formatted_items:
            save_2json(item[5], [item], filename=os.path.join(DATA_DIR, 'inventory.json'))
        return jsonify({'message': 'Inventory saved successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to export entries
@app.route('/export_entries', methods=['POST'])
def export_entries():
    file_name = request.json.get('filename')
    format = request.json.get('format')
    export_inventory(file_name, format)
    return jsonify({'success': True, 'message': 'File successfully created.'}), 200

# Endpoint to clear entries
@app.route('/clear_entries', methods=['POST'])
def clear_entries():
    filename = request.json.get('filename')
    empty_jsonFile(os.path.join(DATA_DIR, filename))
    return jsonify({'message': 'JSON cleared'}), 200

# Endpoint to remove an entry
@app.route('/remove_entry', methods=['POST'])
def remove_entry():
    entry2delete = request.json.get('entry')
    delete_entry(json.dumps(entry2delete))
    return jsonify({'message': 'Entry deleted'}), 200

# Endpoint to check session status
@app.route('/session_status', methods=['GET'])
def session_status():
    result = active_session()
    print('Result:', result)
    return result

# Endpoint to complete session
@app.route('/session_complete', methods=['POST'])
def session_complete():
    return clear_entry()

# Endpoint to start listening
@app.route('/start_listening', methods=['POST'])
def start_listening():
    data = request.json
    for session in data:
        result = start_session(data[session])
    return jsonify({'message': result}), 202

# Endpoint to stop listening
@app.route('/stop_listening', methods=['POST'])
def stop_listening():
    data = request.json
    for session in data:
        result = stop_session(data[session])
    return jsonify({'message': result}), 202


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DATA_DIR, filename, as_attachment=True)
if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    app.run(host=host, port=port, debug=False)