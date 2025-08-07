from models import asset_types_collection

def normalize_asset_data(data):
    return {
        'name': data.get('name', '').strip().title(),
        'category': data.get('category', '').strip().lower(),
        'owner': data.get('owner', '').strip(),
        'status': data.get('status', 'available').strip().lower(),
    }

def get_all_existing_types():
    return sorted(
        [doc["type_name"] for doc in asset_types_collection.find({}, {"type_name": 1})]
    )

def get_asset_statuses():
    return ["available", "assigned", "faulty/repair", "discard"]

def get_master_fields():
    return[
        {"label": "Previous Owner", "name": "prev_owner", "type": "text"},
        {"label": "Username", "name": "username", "type": "text"},
        {"label": "Previous User Code", "name": "prev_user_code", "type": "text"},
        {"label": "User Code", "name": "user_code", "type": "text"},
        {"label": "Area of Collection", "name": "area_of_collection", "type": "text"},
        {"label": "Area", "name": "area", "type": "text"},
        {"label": "State", "name": "state", "type": "select", "options": get_indian_states()},  # 👈 state
        {"label": "Amount", "name": "amount", "type": "number"},
        {"label": "GST (18%)", "name": "gst_18", "type": "number"},
        {"label": "GST (22%)", "name": "gst_22", "type": "number"},
        {"label": "GST (28%)", "name": "gst_28", "type": "number"}, 
        {"label": "Total", "name": "total", "type": "number"},
        {"label": "Date of Purchase", "name": "purchase_date", "type": "date"},
        {"label": "Previous Given Date", "name": "prev_given_date", "type": "date"},
        {"label": "Given Date", "name": "given_date", "type": "date"},
        {"label": "Collected Date", "name": "collected_date", "type": "date"},
        {"label": "Year", "name": "year", "type": "text"},
        {"label": "Status", "name": "status", "type": "select", "options": get_asset_statuses()},
        {"label": "Remarks", "name": "remarks", "type": "text"},
        {"label": "Invoice No.", "name": "invoice_no", "type": "text"},
        {"label": "Vendor", "name": "vendor", "type": "datalist", "options": []},
        {"label": "License", "name": "license", "type": "text"},
        {"label": "MTR Asset Tag", "name": "mtr_asset_tag", "type": "text"},
        {"label": "Asset Tag", "name": "asset_tag", "type": "text"},
        {"label": "Serial No.", "name": "serial_no", "type": "text"},
        {"label": "OS", "name": "os", "type": "datalist", "options": []},
        {"label": "Model", "name": "model", "type": "datalist", "options": []},
        {"label": "System Manufacturer", "name": "system_manufacturer", "type": "datalist", "options": []},        
        {"label": "Domain", "name": "domain", "type": "text"},
        {"label": "IP Address", "name": "ip_address", "type": "text"},
        {"label": "Processor", "name": "processor", "type": "text"},
        {"label": "RAM", "name": "ram", "type": "text"},
        {"label": "Courier by", "name": "courier_by", "type": "text"},
        {"label": "HDD Size", "name": "hdd", "type": "text"},
        {"label": "Free Space", "name": "free_space", "type": "text"},
        {"label": "Endpoint Name", "name": "endpoint_name", "type": "text"},
        {"label": "Received on Approval", "name": "received_on_approval", "type": "text"}
    ]

def get_indian_states():
    return [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    ]

def filter_form_fields(form_data, allowed_fields):
    """
    Returns only fields that are explicitly allowed.
    Skips unrelated/null/default fields.
    """
    return {k: v for k, v in form_data.items() if k in allowed_fields}

def fill_missing_asset_fields(data):
    enriched = data.copy()
    enriched.setdefault('remarks', '')
    enriched.setdefault('status', 'available')
    return enriched
