from flask import Flask, jsonify, request, send_from_directory
import json
import os
from datetime import datetime
import voiceInventory
from voiceInventory import excel_2JSON, start_session, stop_session, active_session, clear_entry, delete_entry, save_2json, export_inventory, empty_jsonFile

app = Flask(__name__)
BASE_DIR = os.environ.get('RENDER_DISK_PATH', os.getcwd())

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)

# Load vendors, materials, and units from JSON files
def load_data():
    with open(os.path.join(BASE_DIR, 'vendors.json')) as vendors_file:
        vendors = json.load(vendors_file)
    with open(os.path.join(BASE_DIR, 'materials.json')) as materials_file:
        materials = json.load(materials_file)
    with open(os.path.join(BASE_DIR, 'units.json')) as units_file:
        units = json.load(units_file)
    return vendors, materials, units

# Endpoint to get vendors, materials, and units
@app.route('/data', methods=['GET'])
def get_data():
    vendors, materials, units = load_data()
    return jsonify({'vendors': vendors, 'materials': materials, 'units': units})

# Endpoint to get vendors
@app.route('/get_vendors', methods=['GET'])
def get_vendors():
    with open(os.path.join(BASE_DIR, 'vendors.json')) as vendors_file:
        vendors = json.load(vendors_file)
    return jsonify({'vendors': vendors})

# Endpoint to get materials
@app.route('/get_materials', methods=['GET'])
def get_materials():
    with open(os.path.join(BASE_DIR, 'materials.json')) as materials_file:
        materials = json.load(materials_file)
    return jsonify({'materials': materials})

# Endpoint to add a new vendor
@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    new_vendor = request.json.get('vendor')
    if new_vendor:
        vendors, materials, units = load_data()
        vendors.append({'vendor': new_vendor})
        with open(os.path.join(BASE_DIR, 'vendors.json'), 'w') as vendors_file:
            json.dump(vendors, vendors_file)
        return jsonify({'message': 'Vendor added successfully!'}), 201
    return jsonify({'error': 'Vendor name is required!'}), 400

# Endpoint to add a new material
@app.route('/add_material', methods=['POST'])
def add_material():
    new_material = request.json.get('material')
    new_unit = request.json.get('unit')
    if new_material:
        vendors, materials, units = load_data()
        materials.append({'material': new_material})
        if new_unit:
            units.append({'unit': new_unit})
        with open(os.path.join(BASE_DIR, 'materials.json'), 'w') as materials_file:
            json.dump(materials, materials_file)
        with open(os.path.join(BASE_DIR, 'units.json'), 'w') as units_file:
            json.dump(units, units_file)
        return jsonify({'message': 'Material with unit added successfully!'}), 201
    return jsonify({'error': 'Material name is required!'}), 400

# Endpoint to delete a vendor
@app.route('/delete_vendor', methods=['POST'])
def delete_vendor():
    vendor_to_delete = request.json.get('vendor')
    if vendor_to_delete:
        vendors, _, _ = load_data()
        updated_vendors = [v for v in vendors if v['vendor'] != vendor_to_delete]
        if len(updated_vendors) < len(vendors):
            with open(os.path.join(BASE_DIR, 'vendors.json'), 'w') as vendors_file:
                json.dump(updated_vendors, vendors_file)
            return jsonify({'success': True, 'message': 'Vendor deleted successfully!'}), 200
        return jsonify({'success': False, 'message': 'Vendor not found!'}), 404
    return jsonify({'success': False, 'message': 'Vendor name is required!'}), 400

# Endpoint to delete a material
@app.route('/delete_material', methods=['POST'])
def delete_material():
    material_to_delete = request.json.get('material')
    if material_to_delete:
        _, materials, _ = load_data()
        updated_materials = [m for m in materials if m['material'] != material_to_delete]
        if len(updated_materials) < len(materials):
            with open(os.path.join(BASE_DIR, 'materials.json'), 'w') as materials_file:
                json.dump(updated_materials, materials_file)
            return jsonify({'success': True, 'message': 'Material deleted successfully!'}), 200
        return jsonify({'success': False, 'message': 'Material not found!'}), 404
    return jsonify({'success': False, 'message': 'Material name is required!'}), 400

# Endpoint to import Excel and convert to JSON
@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided!'}), 400
    file = request.files.get('file')
    output_file = request.form.get('output_file')
    columns = request.form.get('columns').split(',')
    if not file or not output_file or not columns:
        return jsonify({'error': 'Missing file, output_file, or columns!'}), 400
    try:
        temp_path = os.path.join(BASE_DIR, file.filename)
        file.save(temp_path)
        voiceInventory.excel_2JSON(temp_path, os.path.join(BASE_DIR, output_file), *columns)
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
            save_2json(item[5], [item])
        return jsonify({'message': 'Inventory saved successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to export entries
@app.route('/export_entries', methods=['POST'])
def export_entries():
    file_name = request.json.get('filename')
    format_type = request.json.get('format')
    try:
        export_inventory(os.path.join(BASE_DIR, file_name), format_type)
        return jsonify({'success': True, 'message': 'File successfully created.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to clear JSON entries
@app.route('/clear_entries', methods=['POST'])
def clear_entries():
    filename = request.json.get('filename')
    try:
        empty_jsonFile(os.path.join(BASE_DIR, filename))
        return jsonify({'message': 'JSON cleared'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to remove an entry
@app.route('/remove_entry', methods=['POST'])
def remove_entry():
    entry2delete = request.json.get('entry')
    try:
        delete_entry(json.dumps(entry2delete))
        return jsonify({'message': 'Entry deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to check session status
@app.route('/session_status', methods=['GET'])
def session_status():
    result = json.loads(active_session())
    print('Result:', result)
    return jsonify(result)

# Endpoint to complete a session
@app.route('/session_complete', methods=['POST'])
def session_complete():
    try:
        result = clear_entry()
        return jsonify({'message': 'Session cleared', 'entry': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to start listening
@app.route('/start_listening', methods=['POST'])
def start_listening():
    data = request.json
    session_type = data.get('session')
    if not session_type:
        return jsonify({'error': 'Session type is required!'}), 400
    try:
        result = start_session(session_type)
        return jsonify({'message': result}), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to stop listening
@app.route('/stop_listening', methods=['POST'])
def stop_listening():
    data = request.json
    session_type = data.get('session')
    if not session_type:
        return jsonify({'error': 'Session type is required!'}), 400
    try:
        result = stop_session(session_type)
        return jsonify({'message': result}), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to match vendor
@app.route('/match_vendor', methods=['POST'])
def match_vendor_endpoint():
    try:
        vendor_name = request.json.get('vendor')
        if not vendor_name:
            return jsonify({'error': 'Vendor name is required!'}), 400
        df_vendors = voiceInventory.load_json(os.path.join(BASE_DIR, 'vendors.json'))
        matched_vendor = voiceInventory.match_text('vendors', vendor_name, df_vendors)
        if matched_vendor:
            return jsonify({'vendor': matched_vendor}), 200
        return jsonify({'error': 'Vendor not found'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to match material
@app.route('/match_material', methods=['POST'])
def match_material_endpoint():
    try:
        material_name = request.json.get('material')
        if not material_name:
            return jsonify({'error': 'Material name is required!'}), 400
        df_items = voiceInventory.load_json(os.path.join(BASE_DIR, 'materials.json'))
        matched_material = voiceInventory.match_text('materials', material_name, df_items)
        if matched_material:
            return jsonify({'material': matched_material}), 200
        return jsonify({'error': 'Material not found'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint to process quantity
@app.route('/process_quantity', methods=['POST'])
def process_quantity():
    try:
        data = request.json
        text = data.get('text')
        vendor = data.get('vendor')
        material = data.get('material')
        session_type = data.get('session')
        print(f"Received quantity data: text='{text}', vendor='{vendor}', material='{material}', session='{session_type}'")
        if not all([text, vendor, material, session_type]):
            return jsonify({'error': 'Missing required fields!'}), 400
        df_units = voiceInventory.load_json(os.path.join(BASE_DIR, 'units.json'))
        quantity_match = voiceInventory.get_item_quantity(text)
        if quantity_match:
            unit_text, quantity = quantity_match[0]
            unit = voiceInventory.match_text('units', unit_text, df_units) or unit_text or 'undefined'
            print(f"Saving entry: quantity={quantity}, unit={unit}")
            entry = [[
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                vendor,
                material,
                quantity,
                unit,
                session_type
            ]]
            voiceInventory.save_2json(session_type, entry)
            return jsonify({'success': True}), 200
        print(f"Quantity not recognized in text: {text}")
        return jsonify({'success': False, 'error': 'Quantity not recognized. Please say a number like "10" or "5 bags".'}), 400
    except Exception as e:
        print(f"Error in process_quantity: {e}")
        return jsonify({'error': str(e)}), 500

# Endpoint to download files
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(BASE_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))