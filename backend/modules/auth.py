import hashlib
import json
import secrets
from database import query_one, query_all, execute_commit

SECRET_SALT = b"pcware_salt_2026_secure"
ACTIVE_SESSIONS = {}  # token -> user_dict

def hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SECRET_SALT, 100000).hex()

def verify_credentials(identifier: str, password: str):
    hashed = hash_password(password)
    user = query_one("""
        SELECT u.*, r.name as role_name, r.slug as role_slug
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE (u.email = ? OR u.username = ?) AND u.password_hash = ? AND u.is_active = 1
    """, (identifier, identifier, hashed))
    if not user:
        return None
    
    # Fetch permissions
    perms = query_all("""
        SELECT p.module, p.action 
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id = ?
    """, (user["role_id"],))
    user["permissions"] = [f"{p['module']}:{p['action']}" for p in perms]
    
    # Generate token
    token = f"pcw_tok_{secrets.token_hex(24)}"
    ACTIVE_SESSIONS[token] = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role_id": user["role_id"],
        "role_name": user["role_name"],
        "role_slug": user["role_slug"],
        "permissions": user["permissions"]
    }
    return token, ACTIVE_SESSIONS[token]

def get_session_user(token: str):
    return ACTIVE_SESSIONS.get(token)

def register_customer(data: dict):
    email = data.get("email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    address1 = data.get("address_line1", "Customer Address")
    city = data.get("city", "Rajkot")
    pincode = data.get("pincode", "360005")
    company_name = data.get("company_name")
    gstin = data.get("gstin")
    
    if not email or not password or not full_name or not phone:
        raise ValueError("Full name, email, phone, and password are required.")
        
    existing = query_one("SELECT id FROM users WHERE email = ?", (email,))
    if existing:
        raise ValueError("An account with this email already exists.")
        
    pwd_hash = hash_password(password)
    user_id = execute_commit("""
        INSERT INTO users (role_id, username, email, password_hash, full_name, phone, is_active)
        VALUES (8, ?, ?, ?, ?, ?, 1)
    """, (email, email, pwd_hash, full_name, phone))
    
    cust_code = f"CUST-2026-{user_id:04d}"
    cust_id = execute_commit("""
        INSERT INTO customers (user_id, customer_code, full_name, email, phone, company_name, gstin, address_line1, city, state, pincode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Gujarat', ?)
    """, (user_id, cust_code, full_name, email, phone, company_name, gstin, address1, city, pincode))
    
    # Auto-generate unique referral code
    import random
    ref_code = f"PCW-{full_name[:3].upper()}-{random.randint(1000, 9999)}"
    execute_commit("""
        INSERT INTO referral_codes (customer_id, code, points_per_referral, min_order_value, is_active)
        VALUES (?, ?, 500, 10000.0, 1)
    """, (cust_id, ref_code))
    
    return {"user_id": user_id, "customer_id": cust_id, "customer_code": cust_code, "referral_code": ref_code}
