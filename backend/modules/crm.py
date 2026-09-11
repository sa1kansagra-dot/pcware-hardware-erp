import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware_erp.db")
BACKEND_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pcware_production.db")

def get_db():
    target_path = DB_PATH if os.path.exists(DB_PATH) else BACKEND_DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def list_crm_reminders(status_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    if status_filter and status_filter != 'all':
        rows = cursor.execute("SELECT * FROM crm_reminders WHERE status = ? ORDER BY scheduled_date ASC", (status_filter,)).fetchall()
    else:
        rows = cursor.execute("SELECT * FROM crm_reminders ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_crm_reminder(reminder_id, data):
    notes = (data.get("agent_notes") or "Follow-up call completed.").strip()
    rating = int(data.get("rating_given", 5))
    review = (data.get("review_text") or "").strip()

    conn = get_db()
    cursor = conn.cursor()
    rem = cursor.execute("SELECT * FROM crm_reminders WHERE id = ?", (reminder_id,)).fetchone()
    if not rem:
        conn.close()
        raise ValueError(f"CRM Reminder ID {reminder_id} not found.")

    cursor.execute("""
        UPDATE crm_reminders 
        SET status = 'completed', agent_notes = ?, rating_given = ?, review_text = ?
        WHERE id = ?
    """, (notes, rating, review, reminder_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"CRM Follow-up for {rem['customer_name']} completed! Notes and {rating}-star rating saved.",
        "customer_name": rem["customer_name"]
    }

def reschedule_crm_reminder(reminder_id, new_date):
    if not new_date:
        raise ValueError("New follow-up date is required.")

    conn = get_db()
    cursor = conn.cursor()
    rem = cursor.execute("SELECT * FROM crm_reminders WHERE id = ?", (reminder_id,)).fetchone()
    if not rem:
        conn.close()
        raise ValueError(f"CRM Reminder ID {reminder_id} not found.")

    cursor.execute("""
        UPDATE crm_reminders 
        SET scheduled_date = ?, status = 'rescheduled'
        WHERE id = ?
    """, (new_date, reminder_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"CRM Follow-up for {rem['customer_name']} rescheduled to {new_date}.",
        "new_date": new_date
    }
