import json
from datetime import datetime
from database import get_db, query_all, query_one

DEFAULT_CHART_OF_ACCOUNTS = [
    # 10000 ASSETS
    {"code": "10100", "name": "Cash on Hand (Petty Cash)", "type": "ASSET", "subtype": "Cash"},
    {"code": "10210", "name": "HDFC Operating Bank Account", "type": "ASSET", "subtype": "Bank"},
    {"code": "10220", "name": "ICICI Payment Gateway Settlement", "type": "ASSET", "subtype": "Bank"},
    {"code": "12100", "name": "Accounts Receivable (Customers)", "type": "ASSET", "subtype": "Receivable"},
    {"code": "13100", "name": "Input CGST Receivable (9%)", "type": "ASSET", "subtype": "Tax"},
    {"code": "13200", "name": "Input SGST Receivable (9%)", "type": "ASSET", "subtype": "Tax"},
    {"code": "13300", "name": "Input IGST Receivable (18%)", "type": "ASSET", "subtype": "Tax"},
    {"code": "14100", "name": "Inventory - GRN Clearing", "type": "ASSET", "subtype": "Inventory"},
    {"code": "14200", "name": "Inventory Asset - Refurb Hardware", "type": "ASSET", "subtype": "Inventory"},
    {"code": "14250", "name": "Inventory Asset - Custom PCs", "type": "ASSET", "subtype": "Inventory"},
    {"code": "14300", "name": "Inventory Asset - Refurb WIP", "type": "ASSET", "subtype": "Inventory"},
    {"code": "14400", "name": "Inventory Asset - Raw Components", "type": "ASSET", "subtype": "Inventory"},
    {"code": "14500", "name": "Inventory Asset - Assembly WIP", "type": "ASSET", "subtype": "Inventory"},
    {"code": "14600", "name": "Inventory Asset - Consumables & Packaging", "type": "ASSET", "subtype": "Inventory"},
    {"code": "15100", "name": "Diagnostic & Workshop Equipment", "type": "ASSET", "subtype": "Fixed Asset"},

    # 20000 LIABILITIES
    {"code": "20100", "name": "Accounts Payable (Suppliers)", "type": "LIABILITY", "subtype": "Payable"},
    {"code": "21100", "name": "Output CGST Payable (9%)", "type": "LIABILITY", "subtype": "Tax"},
    {"code": "21200", "name": "Output SGST Payable (9%)", "type": "LIABILITY", "subtype": "Tax"},
    {"code": "21300", "name": "Output IGST Payable (18%)", "type": "LIABILITY", "subtype": "Tax"},
    {"code": "22000", "name": "Customer Advances & Deposits", "type": "LIABILITY", "subtype": "Current Liability"},
    {"code": "23000", "name": "Outstanding Referral Rewards Liability", "type": "LIABILITY", "subtype": "Current Liability"},

    # 30000 EQUITY
    {"code": "30100", "name": "Owner Capital & Invested Funds", "type": "EQUITY", "subtype": "Equity"},
    {"code": "30200", "name": "Retained Earnings", "type": "EQUITY", "subtype": "Equity"},

    # 40000 REVENUE
    {"code": "40100", "name": "Hardware Sales Revenue", "type": "REVENUE", "subtype": "Operating Revenue"},
    {"code": "40200", "name": "Custom PC Assembly Revenue", "type": "REVENUE", "subtype": "Operating Revenue"},
    {"code": "40300", "name": "Component & Upgrade Sales Revenue", "type": "REVENUE", "subtype": "Operating Revenue"},
    {"code": "40400", "name": "Repair, Service & Labour Revenue", "type": "REVENUE", "subtype": "Operating Revenue"},
    {"code": "40190", "name": "Sales Returns & Rebates", "type": "REVENUE", "subtype": "Contra Revenue"},

    # 50000 COST OF GOODS SOLD (COGS)
    {"code": "50100", "name": "Cost of Goods Sold - Hardware", "type": "COGS", "subtype": "Direct Cost"},
    {"code": "50200", "name": "Cost of Goods Sold - Custom PCs", "type": "COGS", "subtype": "Direct Cost"},
    {"code": "50300", "name": "Direct Refurbishment Labour Absorbed", "type": "COGS", "subtype": "Labour Recovery"},
    {"code": "50400", "name": "Assembly Labour Absorbed", "type": "COGS", "subtype": "Labour Recovery"},
    {"code": "50500", "name": "Component & Material Consumption", "type": "COGS", "subtype": "Direct Cost"},

    # 60000 OPERATING EXPENSES
    {"code": "60100", "name": "Technician & Staff Salaries", "type": "EXPENSE", "subtype": "Payroll"},
    {"code": "60200", "name": "Workshop Rent & Power Utilities", "type": "EXPENSE", "subtype": "Occupancy"},
    {"code": "60250", "name": "Refurbishment Overhead Absorbed", "type": "EXPENSE", "subtype": "Overhead Recovery"},
    {"code": "60400", "name": "Referral Program Marketing Expense", "type": "EXPENSE", "subtype": "Marketing"},
    {"code": "60450", "name": "Warranty Repair Expense", "type": "EXPENSE", "subtype": "Service"},
    {"code": "60500", "name": "Inventory Loss & Scrap Expense", "type": "EXPENSE", "subtype": "Loss"}
]

def initialize_chart_of_accounts(conn=None):
    """Seed default Chart of Accounts if empty."""
    def _seed(c):
        existing = c.execute("SELECT COUNT(*) as cnt FROM accounts").fetchone()
        if existing["cnt"] == 0:
            for acc in DEFAULT_CHART_OF_ACCOUNTS:
                c.execute("""
                    INSERT INTO accounts (code, name, type, subtype, balance, is_reconciled, is_active)
                    VALUES (?, ?, ?, ?, 0.00, 1, 1)
                """, (acc["code"], acc["name"], acc["type"], acc["subtype"]))
            
            c.execute("""
                INSERT OR IGNORE INTO accounting_periods (fiscal_year, period_name, start_date, end_date, is_closed)
                VALUES ('FY2026-27', 'Annual FY2026-27', '2026-04-01', '2027-03-31', 0)
            """)

    if conn:
        _seed(conn.cursor())
    else:
        with get_db() as c:
            _seed(c.cursor())

def post_journal_entry(conn, entry_number: str, reference_type: str, reference_id: str, memo: str, lines: list, user_id: int = None, posting_date: str = None):
    """
    STRICT DOUBLE-ENTRY INVARIANT:
    1. Sum(Debits) == Sum(Credits) to the exact cent (0.01 tolerance).
    2. Minimum 2 lines required (at least 1 debit, 1 credit).
    3. All debits >= 0, all credits >= 0.
    4. Automatically updates account balances according to normal account balance rules.
    """
    if not lines or len(lines) < 2:
        raise ValueError("Double-entry journal requires at least 2 lines (at least 1 debit and 1 credit).")
        
    posting_date = posting_date or datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    
    # 1. Calculate & verify balance
    total_debit = round(sum(float(line.get("debit", 0.0)) for line in lines), 2)
    total_credit = round(sum(float(line.get("credit", 0.0)) for line in lines), 2)
    
    diff = abs(round(total_debit - total_credit, 2))
    if diff > 0.01:
        raise ValueError(
            f"DOUBLE_ENTRY_IMBALANCE: Journal {entry_number} is unbalanced! "
            f"Total Debit: ₹{total_debit:.2f} != Total Credit: ₹{total_credit:.2f} (Discrepancy: ₹{diff:.2f})"
        )
        
    # 2. Insert Journal Header
    cursor.execute("""
        INSERT INTO journals (entry_number, posting_date, reference_type, reference_id, memo, total_debit, total_credit, is_posted, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (entry_number, posting_date, reference_type, str(reference_id), memo, total_debit, total_credit, user_id))
    journal_id = cursor.lastrowid
    
    # 3. Process each journal line and update account balance
    for idx, line in enumerate(lines):
        acc_code = str(line.get("account_code", "")).strip()
        debit = round(float(line.get("debit", 0.0)), 2)
        credit = round(float(line.get("credit", 0.0)), 2)
        line_memo = line.get("line_memo", memo)
        
        if debit < 0 or credit < 0:
            raise ValueError(f"Debit and Credit must be non-negative numbers on line {idx+1}.")
            
        if debit == 0 and credit == 0:
            continue
            
        acc = cursor.execute("SELECT id, type, balance FROM accounts WHERE code = ?", (acc_code,)).fetchone()
        if not acc:
            raise ValueError(f"Account code '{acc_code}' not found in Chart of Accounts.")
            
        acc_id = acc["id"]
        acc_type = acc["type"]
        current_bal = float(acc["balance"])
        
        # Balance formula:
        # ASSET, EXPENSE, COGS: normal balance is Debit (Debit increases, Credit decreases)
        # LIABILITY, EQUITY, REVENUE: normal balance is Credit (Credit increases, Debit decreases)
        if acc_type in ("ASSET", "EXPENSE", "COGS"):
            new_bal = round(current_bal + debit - credit, 2)
        else:
            new_bal = round(current_bal + credit - debit, 2)
            
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_bal, acc_id))
        
        cursor.execute("""
            INSERT INTO journal_lines (journal_id, account_id, debit, credit, line_memo)
            VALUES (?, ?, ?, ?, ?)
        """, (journal_id, acc_id, debit, credit, line_memo))
        
    # 4. Record in audit_logs
    cursor.execute("""
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, new_value_json)
        VALUES (?, 'POST_JOURNAL', 'journals', ?, ?)
    """, (user_id, str(journal_id), json.dumps({
        "entry_number": entry_number,
        "ref": f"{reference_type}:{reference_id}",
        "debit": total_debit,
        "credit": total_credit,
        "lines": len(lines)
    })))
    
    return {
        "journal_id": journal_id,
        "entry_number": entry_number,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "lines_count": len(lines)
    }

def get_chart_of_accounts():
    """Returns full hierarchical Chart of Accounts with live balances."""
    initialize_chart_of_accounts()
    accounts = query_all("""
        SELECT * FROM accounts 
        ORDER BY code ASC
    """)
    return accounts

def get_trial_balance():
    """
    Calculates Trial Balance across all active accounts.
    Verifies Sum(Debits) == Sum(Credits).
    """
    initialize_chart_of_accounts()
    with get_db() as conn:
        c = conn.cursor()
        
        rows = c.execute("""
            SELECT a.id, a.code, a.name, a.type, a.subtype, a.balance,
                   COALESCE(SUM(jl.debit), 0.0) as total_debit,
                   COALESCE(SUM(jl.credit), 0.0) as total_credit
            FROM accounts a
            LEFT JOIN journal_lines jl ON a.id = jl.account_id
            GROUP BY a.id
            ORDER BY a.code ASC
        """).fetchall()
        
        total_dr = 0.0
        total_cr = 0.0
        tb_lines = []
        
        for r in rows:
            acc_type = r["type"]
            bal = float(r["balance"])
            dr_amount = 0.0
            cr_amount = 0.0
            
            if acc_type in ("ASSET", "EXPENSE", "COGS"):
                if bal >= 0:
                    dr_amount = bal
                else:
                    cr_amount = abs(bal)
            else:
                if bal >= 0:
                    cr_amount = bal
                else:
                    dr_amount = abs(bal)
                    
            total_dr += dr_amount
            total_cr += cr_amount
            
            tb_lines.append({
                "code": r["code"],
                "name": r["name"],
                "type": r["type"],
                "subtype": r["subtype"],
                "debit": round(dr_amount, 2),
                "credit": round(cr_amount, 2)
            })
            
        total_dr = round(total_dr, 2)
        total_cr = round(total_cr, 2)
        diff = round(abs(total_dr - total_cr), 2)
        is_balanced = (diff <= 0.01)
        
        return {
            "is_balanced": is_balanced,
            "discrepancy": diff,
            "total_debit": total_dr,
            "total_credit": total_cr,
            "accounts": tb_lines,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def get_general_ledger(account_code: str = None, from_date: str = None, to_date: str = None):
    """Drill-down transaction ledger with running balance."""
    query = """
        SELECT jl.id as line_id, j.entry_number, j.posting_date, j.reference_type, j.reference_id, 
               j.memo, a.code as account_code, a.name as account_name, a.type as account_type,
               jl.debit, jl.credit, jl.line_memo
        FROM journal_lines jl
        JOIN journals j ON jl.journal_id = j.id
        JOIN accounts a ON jl.account_id = a.id
        WHERE 1=1
    """
    params = []
    if account_code:
        query += " AND a.code = ?"
        params.append(account_code)
    if from_date:
        query += " AND j.posting_date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND j.posting_date <= ?"
        params.append(to_date)
        
    query += " ORDER BY j.posting_date ASC, j.id ASC, jl.id ASC"
    
    entries = query_all(query, tuple(params))
    return entries

def get_profit_and_loss(from_date: str = None, to_date: str = None):
    """
    Calculates dynamic Profit & Loss statement:
    Revenue - Cost of Goods Sold = Gross Profit
    Gross Profit - Operating Expenses = Net Profit
    """
    initialize_chart_of_accounts()
    with get_db() as conn:
        c = conn.cursor()
        
        accounts = c.execute("""
            SELECT code, name, type, subtype, balance 
            FROM accounts 
            WHERE type IN ('REVENUE', 'COGS', 'EXPENSE')
            ORDER BY code ASC
        """).fetchall()
        
        revenue_items = []
        cogs_items = []
        expense_items = []
        
        total_revenue = 0.0
        total_cogs = 0.0
        total_expense = 0.0
        
        for acc in accounts:
            bal = float(acc["balance"])
            item = {"code": acc["code"], "name": acc["name"], "subtype": acc["subtype"], "amount": bal}
            
            if acc["type"] == "REVENUE":
                if acc["code"] == "40190":  # Contra Revenue (Returns)
                    total_revenue -= bal
                    item["amount"] = -bal
                else:
                    total_revenue += bal
                revenue_items.append(item)
                
            elif acc["type"] == "COGS":
                total_cogs += bal
                cogs_items.append(item)
                
            elif acc["type"] == "EXPENSE":
                total_expense += bal
                expense_items.append(item)
                
        gross_profit = round(total_revenue - total_cogs, 2)
        net_profit = round(gross_profit - total_expense, 2)
        
        return {
            "period": f"All time (up to {datetime.now().strftime('%Y-%m-%d')})",
            "revenue": {
                "items": revenue_items,
                "total": round(total_revenue, 2)
            },
            "cogs": {
                "items": cogs_items,
                "total": round(total_cogs, 2)
            },
            "gross_profit": gross_profit,
            "gross_margin_pct": round((gross_profit / total_revenue * 100.0) if total_revenue > 0 else 0.0, 2),
            "expenses": {
                "items": expense_items,
                "total": round(total_expense, 2)
            },
            "net_profit": net_profit,
            "net_margin_pct": round((net_profit / total_revenue * 100.0) if total_revenue > 0 else 0.0, 2)
        }

def get_balance_sheet(as_of_date: str = None):
    """
    Computes Balance Sheet:
    Total Assets == Total Liabilities + Total Equity (including Net Profit)
    """
    initialize_chart_of_accounts()
    with get_db() as conn:
        c = conn.cursor()
        
        accounts = c.execute("""
            SELECT code, name, type, subtype, balance 
            FROM accounts 
            WHERE type IN ('ASSET', 'LIABILITY', 'EQUITY')
            ORDER BY code ASC
        """).fetchall()
        
        current_assets = []
        inventory_assets = []
        fixed_assets = []
        liabilities = []
        equity_items = []
        
        tot_curr_assets = 0.0
        tot_inv_assets = 0.0
        tot_fixed_assets = 0.0
        tot_liabilities = 0.0
        tot_equity = 0.0
        
        for acc in accounts:
            bal = float(acc["balance"])
            item = {"code": acc["code"], "name": acc["name"], "subtype": acc["subtype"], "amount": bal}
            
            if acc["type"] == "ASSET":
                if acc["subtype"] == "Inventory":
                    inventory_assets.append(item)
                    tot_inv_assets += bal
                elif acc["subtype"] == "Fixed Asset":
                    fixed_assets.append(item)
                    tot_fixed_assets += bal
                else:
                    current_assets.append(item)
                    tot_curr_assets += bal
                    
            elif acc["type"] == "LIABILITY":
                liabilities.append(item)
                tot_liabilities += bal
                
            elif acc["type"] == "EQUITY":
                equity_items.append(item)
                tot_equity += bal
                
        pl = get_profit_and_loss()
        current_net_profit = pl["net_profit"]
        equity_items.append({
            "code": "30300",
            "name": "Current Year Retained Profit / Loss",
            "subtype": "Current Earnings",
            "amount": current_net_profit
        })
        tot_equity += current_net_profit
        
        total_assets = round(tot_curr_assets + tot_inv_assets + tot_fixed_assets, 2)
        total_liabilities_equity = round(tot_liabilities + tot_equity, 2)
        diff = round(abs(total_assets - total_liabilities_equity), 2)
        
        return {
            "as_of_date": as_of_date or datetime.now().strftime("%Y-%m-%d"),
            "assets": {
                "current_assets": current_assets,
                "inventory_assets": inventory_assets,
                "fixed_assets": fixed_assets,
                "total_current": round(tot_curr_assets, 2),
                "total_inventory": round(tot_inv_assets, 2),
                "total_fixed": round(tot_fixed_assets, 2),
                "total_assets": total_assets
            },
            "liabilities": {
                "items": liabilities,
                "total_liabilities": round(tot_liabilities, 2)
            },
            "equity": {
                "items": equity_items,
                "total_equity": round(tot_equity, 2)
            },
            "total_liabilities_and_equity": total_liabilities_equity,
            "is_balanced": (diff <= 0.01),
            "discrepancy": diff
        }
