import os
import json
import base64
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global local-fallback file path
MOCK_DB_PATH = 'mock_sheets_db.json'

def get_sheets_client():
    creds_b64 = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
    
    if not creds_b64 or not SPREADSHEET_ID:
        # Try local credentials.json file fallback
        if os.path.exists('credentials.json') and SPREADSHEET_ID:
            try:
                import gspread
                scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                return gspread.service_account(filename='credentials.json', scopes=scopes)
            except Exception as e:
                logging.error(f"Local credentials.json service authorization failed: {e}")
        
        logging.info("Google Sheets credentials not set. Operating in Local Mock File DB Mode.")
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        creds_json = base64.b64decode(creds_b64).decode('utf-8')
        creds_dict = json.loads(creds_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        logging.error(f"Failed to authorize Google Sheets client from base64 env: {e}")
        return None

# --- Mock Local Database Handlers ---
def _load_mock_db():
    if not os.path.exists(MOCK_DB_PATH):
        default_db = {
            "affiliates": [],
            "deals": [],
            "promo_codes": [],
            "clicks": [],
            "conversions": [],
            "payout_requests": []
        }
        with open(MOCK_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(MOCK_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to parse mock DB JSON: {e}")
        return {"affiliates": [], "deals": [], "promo_codes": [], "clicks": [], "conversions": [], "payout_requests": []}

def _save_mock_db(db):
    try:
        with open(MOCK_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
    except Exception as e:
        logging.error(f"Failed writing mock DB JSON: {e}")

# --- Sheets CRUD Interfaces ---
def register_influencer(handle, email, display_name, payment_method, payment_account, pin_hash, bio="", profile_image="", banner_image="", social_instagram="", social_tiktok="", social_youtube=""):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    
    timestamp = datetime.utcnow().isoformat()
    record = {
        "handle": handle.lower().strip(),
        "email": email.strip(),
        "display_name": display_name.strip(),
        "bio": bio,
        "profile_image": profile_image,
        "banner_image": banner_image,
        "social_instagram": social_instagram,
        "social_tiktok": social_tiktok,
        "social_youtube": social_youtube,
        "payment_method": payment_method,
        "payment_account": payment_account,
        "pin_hash": pin_hash,
        "created_at": timestamp,
        "status": "active",
        "total_clicks": 0,
        "total_bookings": 0,
        "total_earned": 0.0,
        "paid_earned": 0.0,
        "pending_earned": 0.0
    }

    if not client:
        # Local Mock Storage
        db = _load_mock_db()
        # Verify handle uniqueness
        if any(a["handle"] == record["handle"] for a in db["affiliates"]):
            return False, "Handle already registered."
        db["affiliates"].append(record)
        _save_mock_db(db)
        return True, "Successfully registered locally."

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('affiliates')
        
        # Check uniqueness in spreadsheet
        all_handles = sheet.col_values(1)[1:] # skip header
        if record["handle"] in [h.lower() for h in all_handles]:
            return False, "Handle already registered."
            
        row = [
            record["handle"], record["email"], record["display_name"], record["bio"],
            record["profile_image"], record["banner_image"], record["social_instagram"],
            record["social_tiktok"], record["social_youtube"], record["payment_method"],
            record["payment_account"], record["pin_hash"], record["created_at"],
            record["status"], record["total_clicks"], record["total_bookings"],
            record["total_earned"], record["paid_earned"], record["pending_earned"]
        ]
        sheet.append_row(row)
        return True, "Successfully registered in Google Sheets."
    except Exception as e:
        logging.error(f"Google Sheets registration failed: {e}")
        return False, str(e)

def get_influencer(handle):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    handle_lower = handle.lower().strip()

    if not client:
        db = _load_mock_db()
        aff = next((a for a in db["affiliates"] if a["handle"] == handle_lower), None)
        return aff

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('affiliates')
        records = sheet.get_all_records()
        for r in records:
            if str(r.get("handle", "")).lower().strip() == handle_lower:
                return r
    except Exception as e:
        logging.error(f"Google Sheets read failed for handle {handle}: {e}")
    return None

def update_influencer_profile(handle, display_name, bio, instagram, tiktok, youtube, profile_image="", banner_image=""):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    handle_lower = handle.lower().strip()

    if not client:
        db = _load_mock_db()
        for a in db["affiliates"]:
            if a["handle"] == handle_lower:
                a["display_name"] = display_name
                a["bio"] = bio
                a["social_instagram"] = instagram
                a["social_tiktok"] = tiktok
                a["social_youtube"] = youtube
                if profile_image: a["profile_image"] = profile_image
                if banner_image: a["banner_image"] = banner_image
                break
        _save_mock_db(db)
        return True

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('affiliates')
        records = sheet.get_all_records()
        for idx, r in enumerate(records):
            if str(r.get("handle", "")).lower().strip() == handle_lower:
                # Row number is idx + 2 (1-based, plus 1 for header)
                row_num = idx + 2
                sheet.update_cell(row_num, 3, display_name) # display_name
                sheet.update_cell(row_num, 4, bio)          # bio
                if profile_image: sheet.update_cell(row_num, 5, profile_image)
                if banner_image: sheet.update_cell(row_num, 6, banner_image)
                sheet.update_cell(row_num, 7, instagram)    # social_instagram
                sheet.update_cell(row_num, 8, tiktok)       # social_tiktok
                sheet.update_cell(row_num, 9, youtube)      # social_youtube
                return True
    except Exception as e:
        logging.error(f"Google Sheets profile update failed: {e}")
    return False

# --- Deals CRUD ---
def add_deal(handle, title, original_url, wrapped_url, code, category, description="", expires_at=""):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    deal_id = "DEAL_" + str(int(datetime.utcnow().timestamp() * 1000))
    
    record = {
        "handle": handle.lower().strip(),
        "deal_id": deal_id,
        "title": title.strip(),
        "original_url": original_url.strip(),
        "wrapped_url": wrapped_url.strip(),
        "code": code.strip(),
        "category": category,
        "description": description,
        "expires_at": expires_at or "Never",
        "is_active": True
    }

    if not client:
        db = _load_mock_db()
        db["deals"].append(record)
        _save_mock_db(db)
        return deal_id

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('deals')
        row = [
            record["handle"], record["deal_id"], record["title"], record["original_url"],
            record["wrapped_url"], record["code"], record["category"], record["description"],
            record["expires_at"], record["is_active"]
        ]
        sheet.append_row(row)
        return deal_id
    except Exception as e:
        logging.error(f"Google Sheets deal write failed: {e}")
    return None

def get_deal(handle, deal_id):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    
    if not client:
        db = _load_mock_db()
        return next((d for d in db["deals"] if d["handle"] == handle.lower() and d["deal_id"] == deal_id), None)
        
    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('deals')
        records = sheet.get_all_records()
        for r in records:
            if str(r.get("handle", "")).lower() == handle.lower() and str(r.get("deal_id", "")) == deal_id:
                return r
    except Exception as e:
        logging.error(f"Google Sheets read failed for deal {deal_id}: {e}")
    return None

def get_influencer_deals(handle):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    handle_lower = handle.lower().strip()

    if not client:
        db = _load_mock_db()
        return [d for d in db["deals"] if d["handle"] == handle_lower and d.get("is_active", True)]

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('deals')
        records = sheet.get_all_records()
        deals = []
        for r in records:
            if str(r.get("handle", "")).lower() == handle_lower and r.get("is_active") in [True, "TRUE", 1, "1"]:
                deals.append(r)
        return deals
    except Exception as e:
        logging.error(f"Google Sheets read failed for influencer deals {handle}: {e}")
    return []

def delete_deal(handle, deal_id):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    handle_lower = handle.lower().strip()

    if not client:
        db = _load_mock_db()
        db["deals"] = [d for d in db["deals"] if not (d["handle"] == handle_lower and d["deal_id"] == deal_id)]
        _save_mock_db(db)
        return True

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('deals')
        records = sheet.get_all_records()
        for idx, r in enumerate(records):
            if str(r.get("handle", "")).lower() == handle_lower and str(r.get("deal_id", "")) == deal_id:
                sheet.delete_rows(idx + 2) # 2 offset
                return True
    except Exception as e:
        logging.error(f"Google Sheets delete deal failed: {e}")
    return False

# --- Clicks & Conversions ---
def log_affiliate_click(click_id, handle, deal_title, ip=""):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    timestamp = datetime.utcnow().isoformat()

    record = {
        "click_id": click_id,
        "handle": handle.lower().strip(),
        "deal_title": deal_title,
        "clicked_at": timestamp,
        "ip": ip
    }

    if not client:
        db = _load_mock_db()
        db["clicks"].append(record)
        # Update clicks stats on influencer profile
        for a in db["affiliates"]:
            if a["handle"] == handle.lower().strip():
                a["total_clicks"] += 1
                break
        _save_mock_db(db)
        return

    try:
        # Log click
        sheet = client.open_by_key(spreadsheet_id).worksheet('clicks')
        sheet.append_row([click_id, handle.lower().strip(), deal_title, timestamp, ip])
        
        # Increment total clicks count on affiliates profile
        aff_sheet = client.open_by_key(spreadsheet_id).worksheet('affiliates')
        records = aff_sheet.get_all_records()
        for idx, r in enumerate(records):
            if str(r.get("handle", "")).lower().strip() == handle.lower().strip():
                clicks = int(r.get("total_clicks", 0)) + 1
                aff_sheet.update_cell(idx + 2, 15, clicks) # column 15 = total_clicks
                break
    except Exception as e:
        logging.error(f"Google Sheets click logging failed: {e}")

# --- Payout Requests ---
def request_payout(handle, amount, payment_method, payment_account):
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    payout_id = "PAYOUT_" + str(int(datetime.utcnow().timestamp()))
    timestamp = datetime.utcnow().isoformat()
    
    record = {
        "payout_id": payout_id,
        "handle": handle.lower().strip(),
        "amount": amount,
        "method": payment_method,
        "account": payment_account,
        "status": "pending",
        "requested_at": timestamp,
        "paid_at": ""
    }

    if not client:
        db = _load_mock_db()
        db["payout_requests"].append(record)
        _save_mock_db(db)
        return True

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('payout_requests')
        row = [payout_id, handle.lower().strip(), amount, payment_method, payment_account, "pending", timestamp, ""]
        sheet.append_row(row)
        return True
    except Exception as e:
        logging.error(f"Google Sheets payout request failed: {e}")
    return False

# --- Admin Operations ---
def get_payout_requests():
    client = get_sheets_client()
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    
    if not client:
        db = _load_mock_db()
        return db["payout_requests"]
        
    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet('payout_requests')
        return sheet.get_all_records()
    except Exception as e:
        logging.error(f"Google Sheets read payout requests failed: {e}")
    return []
