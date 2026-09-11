from datetime import datetime
from database import query_all, query_one, execute_commit, get_db

def get_or_create_referral_code(customer_id: int):
    code_row = query_one("""
        SELECT * FROM referral_codes WHERE customer_id = ? AND is_active = 1
    """, (customer_id,))
    
    if not code_row:
        cust = query_one("SELECT full_name FROM customers WHERE id = ?", (customer_id,))
        name_prefix = (cust["full_name"][:3].upper() if cust else "PCW")
        import random
        new_code = f"PCW-{name_prefix}-{random.randint(1000, 9999)}"
        cid = execute_commit("""
            INSERT INTO referral_codes (customer_id, code, points_per_referral, min_order_value, is_active)
            VALUES (?, ?, 500, 10000.0, 1)
        """, (customer_id, new_code))
        code_row = query_one("SELECT * FROM referral_codes WHERE id = ?", (cid,))
        
    # Get current ledger balance
    last_ledger = query_one("""
        SELECT running_balance FROM referral_point_ledger
        WHERE customer_id = ?
        ORDER BY id DESC LIMIT 1
    """, (customer_id,))
    available_points = last_ledger["running_balance"] if last_ledger else 0
    
    # Get referred customers count
    referrals_count = query_one("""
        SELECT COUNT(*) as cnt FROM referral_relationships
        WHERE referrer_customer_id = ?
    """, (customer_id,))
    
    # Get ledger history
    ledger_history = query_all("""
        SELECT * FROM referral_point_ledger
        WHERE customer_id = ?
        ORDER BY id DESC
    """, (customer_id,))
    
    return {
        "referral_code": code_row["code"],
        "points_per_referral": code_row["points_per_referral"],
        "min_order_value": code_row["min_order_value"],
        "available_points": available_points,
        "total_referrals": referrals_count["cnt"] if referrals_count else 0,
        "ledger": ledger_history
    }

def record_referral_reward(referral_code_str: str, buyer_customer_id: int, order_id: int, order_total: float):
    """
    Rule 7: Referral points must use an immutable transaction ledger.
    """
    code_row = query_one("""
        SELECT rc.*, c.id as referrer_id, c.full_name as referrer_name
        FROM referral_codes rc
        JOIN customers c ON rc.customer_id = c.id
        WHERE UPPER(rc.code) = ? AND rc.is_active = 1
    """, (referral_code_str.strip().upper(),))
    
    if not code_row:
        return {"status": "ignored", "reason": "Invalid referral code"}
        
    referrer_id = code_row["referrer_id"]
    if referrer_id == buyer_customer_id:
        return {"status": "ignored", "reason": "Self-referral not permitted"}
        
    if order_total < code_row["min_order_value"]:
        return {"status": "ignored", "reason": f"Order total under min threshold ₹{code_row['min_order_value']}"}
        
    points_to_award = code_row["points_per_referral"]
    
    with get_db() as conn:
        c = conn.cursor()
        
        # Link relationship
        c.execute("""
            INSERT INTO referral_relationships (referrer_customer_id, referred_customer_id, referral_code_id, status, first_order_id)
            VALUES (?, ?, ?, 'rewarded', ?)
        """, (referrer_id, buyer_customer_id, code_row["id"], order_id))
        rel_id = c.lastrowid
        
        # Calculate new running balance for Referrer
        last_row = c.execute("""
            SELECT running_balance FROM referral_point_ledger
            WHERE customer_id = ? ORDER BY id DESC LIMIT 1
        """, (referrer_id,)).fetchone()
        
        prev_balance = last_row["running_balance"] if last_row else 0
        new_balance = prev_balance + points_to_award
        
        # Append immutable credit row
        c.execute("""
            INSERT INTO referral_point_ledger (customer_id, transaction_type, points_in, points_out, 
                                              running_balance, sales_order_id, referral_relationship_id, reason)
            VALUES (?, 'earned_referral', ?, 0, ?, ?, ?, ?)
        """, (referrer_id, points_to_award, new_balance, order_id, rel_id, 
                f"Referral reward credited for referred purchase #{order_id}"))
                
    return {
        "status": "rewarded",
        "referrer_id": referrer_id,
        "points_awarded": points_to_award,
        "new_balance": new_balance
    }

def redeem_points(customer_id: int, points: int, order_id: int):
    if points <= 0:
        return
        
    with get_db() as conn:
        c = conn.cursor()
        
        last_row = c.execute("""
            SELECT running_balance FROM referral_point_ledger
            WHERE customer_id = ? ORDER BY id DESC LIMIT 1
        """, (customer_id,)).fetchone()
        
        current_balance = last_row["running_balance"] if last_row else 0
        if current_balance < points:
            raise ValueError(f"Insufficient referral points balance. Available: {current_balance}, Requested: {points}")
            
        new_balance = current_balance - points
        
        # Append immutable debit row
        c.execute("""
            INSERT INTO referral_point_ledger (customer_id, transaction_type, points_in, points_out, 
                                              running_balance, sales_order_id, reason)
            VALUES (?, 'redeemed_discount', 0, ?, ?, ?, ?)
        """, (customer_id, points, new_balance, order_id, f"Redeemed {points} points on Order #{order_id}"))
        
    return {"redeemed": points, "remaining_balance": new_balance}
