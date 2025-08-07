from flask import Blueprint, request, render_template, session, redirect, url_for, flash, jsonify, send_from_directory
from bson.objectid import ObjectId
from datetime import datetime
from models import assets_collection, asset_types_collection
from forms import AssetForm
from utils import normalize_asset_data, get_master_fields, get_indian_states
from utils import get_all_existing_types 

#from utils import normalize_asset_data, fill_missing_asset_fields, get_master_fields, get_indian_states, filter_form_fields
#from bson import json_util
#import json

main_bp = Blueprint('main', __name__)

def parse_ddmmyyyy_to_date(val):
    try:
        return datetime.strptime(val.strip(), "%d-%m-%Y") if val else None
    except Exception:
        return None
    
@main_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('public/assets', filename)


@main_bp.route('/')
def landing():
    return render_template('landing.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    assets = list(assets_collection.find())
    return render_template('dashboard.html', assets=assets)

@main_bp.route("/create_type", methods=["POST"])
def create_type():
    data = request.json
    type_name = data.get("type")
    fields = data.get("fields", [])

    if not type_name or not fields:
        return jsonify(success=False, message="Type name and fields are required."), 400

    if asset_types_collection.find_one({"type_name": type_name}):
        return jsonify(success=False, message="Type already exists."), 409

    asset_types_collection.insert_one({
        "type_name": type_name,
        "fields": fields
    })

    return jsonify(success=True, message="Type created successfully.")

@main_bp.route('/get_asset_types')
def get_asset_types():
    types = asset_types_collection.find({}, {"_id": 0, "type_name": 1})
    return jsonify([doc["type_name"] for doc in types])

@main_bp.route('/get_fields/<asset_type>')
def get_fields(asset_type):
    config = asset_types_collection.find_one({'type_name': asset_type})
    if config and 'fields' in config:
        fields = config["fields"]

        status_options = ["Available", "Assigned", "Repair/Faulty", "Discard"]

        for field in fields:
            if field.get("name", "").lower() == "state" and field.get("type") == "select":
                if not field.get("options"):
                    field["options"] = get_indian_states()

            if field.get("name", "").lower() == "status" and field.get("type") == "select":
                if not field.get("options"):
                    field["options"] = status_options

        return jsonify({"fields": fields})

    # ✅ Always return fields key to avoid frontend error
    return jsonify({"fields": []})


@main_bp.route("/get_master_fields")
def get_master_fields_api():
    return jsonify({"fields": get_master_fields()})

@main_bp.route("/create_asset", methods=["GET", "POST"])
def create_asset():
    form = AssetForm()

    if request.method == "POST":
        raw_data = request.form.to_dict()
        raw_data.pop("csrf_token", None)
        raw_data.pop("submit", None)

        selected_type = raw_data.get("category", "")
        new_type = raw_data.get("new_type", "").strip()
        is_new_type = selected_type == "add_new_type" and new_type

        custom_fields = []

        if is_new_type:
            selected_type = new_type
            raw_data["category"] = new_type

            # Parse selected features
            predefined_fields_raw = request.form.get("selected_features", "")
            predefined_fields = [f.strip() for f in predefined_fields_raw.split(",") if f.strip()]

            # Parse custom fields
            custom_fields_raw = request.form.get("custom_fields", "")
            for item in custom_fields_raw.split("|"):
                if not item.strip():
                    continue
                try:
                    label, name, ftype = item.strip().split(":", 2)
                    custom_fields.append({"label": label, "name": name, "type": ftype})
                except ValueError:
                    continue

            # Combine field list
            master_fields = get_master_fields()
            print("📦 master_fields available:", [f["name"] for f in master_fields])
            full_predefined = [f for f in master_fields if f["name"] in predefined_fields]
            new_type_fields = full_predefined + custom_fields

            print("🧪 new_type_fields about to be saved:", new_type_fields)

            # Save the new type to DB
            asset_types_collection.update_one(
                {"type_name": new_type},
                {"$set": {"fields": new_type_fields}},
                upsert=True
            )

        # ✅ Fetch config AFTER type is saved
        if is_new_type:
            fields_to_render = new_type_fields
        else:
            selected_config = asset_types_collection.find_one({"type_name": selected_type})
            fields_to_render = selected_config["fields"] if selected_config else []

        allowed_fields = [f["name"] for f in fields_to_render]


        for field in ["given_date", "purchase_date", "collected_date", "prev_given_date"]:
            date_str = raw_data.get(field, "")
            parsed_date = parse_ddmmyyyy_to_date(date_str.strip()) if date_str.strip() else None
            if parsed_date:
                raw_data[field] = parsed_date.strftime("%d-%m-%Y")
            else:
                raw_data[field] = date_str

        for money_field in ["amount", "total"]:
            if raw_data.get(money_field):
                raw_data[money_field] = raw_data[money_field].replace("₹", "").replace(",", "")

        normalized = normalize_asset_data(raw_data)
        raw_data.update(normalized)

        print("⚙️ raw_data keys:", raw_data.keys())
        print("⚙️ allowed_fields:", allowed_fields)

        payload = {
            k: (v if isinstance(v, str) else v.strftime("%d-%m-%Y") if isinstance(v, datetime) else "")
            for k, v in raw_data.items()
            if k in allowed_fields
        }

        # Ensure all allowed fields are present, even if empty
        for field_name in allowed_fields:
            payload.setdefault(field_name, "")

        payload["category"] = selected_type

        print("➡️ Payload to insert:", payload)

        assets_collection.insert_one(payload)

        flash("Asset added successfully.", "success")
        return redirect(url_for("main.dashboard"))

    # GET route: Populate dropdown and form
    types = asset_types_collection.find({}, {"type_name": 1})
    form.category.choices = [(t["type_name"], t["type_name"]) for t in types]
    form.category.choices.append(("add_new_type", "add_new_type"))

    selected_type = request.args.get("type")
    fields_to_render = []

    if selected_type == "add_new_type":
        fields_to_render = get_master_fields()
        for field in fields_to_render:
            if field.get("name", "").lower() == "state" and field.get("type") == "select":
                if not field.get("options"):
                    field["options"] = get_indian_states()
    elif selected_type:
        config = asset_types_collection.find_one({"type_name": selected_type})
        if config and "fields" in config:
            fields_to_render = config["fields"]

    return render_template(
        "create_new_asset.html",
        form=form,
        editing=False,
        master_fields=get_master_fields(),
        asset_data={},
        fields_to_render=fields_to_render
    )

@main_bp.route("/edit_asset/<asset_id>", methods=["GET", "POST"])
def edit_asset(asset_id):
    asset = assets_collection.find_one({"_id": ObjectId(asset_id)})
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for("main.dashboard"))

    selected_type = asset.get("category")
    config = asset_types_collection.find_one({"type_name": selected_type})
    fields_to_render = config["fields"] if config else []
    allowed_fields = [f["name"] for f in fields_to_render]

    form = AssetForm(data=asset)

    if request.method == "POST":
        raw_data = request.form.to_dict()
        raw_data.pop("csrf_token", None)
        raw_data.pop("submit", None)

        for field in ["given_date", "purchase_date", "collected_date", "prev_given_date"]:
            date_str = raw_data.get(field, "")
            parsed_date = parse_ddmmyyyy_to_date(date_str.strip()) if date_str.strip() else None
            if parsed_date:
                raw_data[field] = parsed_date.strftime("%d-%m-%Y")
            else:
                raw_data[field] = date_str

        for money_field in ["amount", "total"]:
            if raw_data.get(money_field):
                raw_data[money_field] = raw_data[money_field].replace("₹", "").replace(",", "")

        normalized = normalize_asset_data(raw_data)
        raw_data.update(normalized)

        payload = {
            k: (v if isinstance(v, str) else v.strftime("%d-%m-%Y") if isinstance(v, datetime) else "")
            for k, v in raw_data.items()
            if k in allowed_fields
        }

        for key in allowed_fields:
            payload.setdefault(key, "")

        payload["category"] = selected_type

        assets_collection.update_one({"_id": ObjectId(asset_id)}, {"$set": payload})

        flash("Asset updated successfully.", "success")
        return redirect(url_for("main.dashboard"))

    asset["_id"] = str(asset["_id"]) 
    return render_template(
        "create_new_asset.html",
        form=form,
        editing=True,
        master_fields=get_master_fields(),
        asset_data=asset,
        asset_id=asset_id,
        fields_to_render=fields_to_render,
        types=get_all_existing_types()

    )


@main_bp.route("/view_asset/<asset_id>")
def view_asset(asset_id):
    asset = assets_collection.find_one({"_id": ObjectId(asset_id)})
    if not asset:
        flash("Asset not found", "danger")
        return redirect(url_for("main.dashboard"))

    asset_type = asset.get("category")
    fields_config = []

    config = asset_types_collection.find_one({"type_name": asset_type})
    if config:
        fields_config = config.get("fields", [])

    view_data = []
    for field in fields_config:
        key = field.get("name")
        label = field.get("label")
        value = asset.get(key, "")

        if isinstance(value, float):
            value = f"₹{value:,.2f}"

        view_data.append({
            "label": label,
            "value": value if value != "" else "—"
        })

    return render_template("view_asset.html", asset=asset, view_data=view_data)
