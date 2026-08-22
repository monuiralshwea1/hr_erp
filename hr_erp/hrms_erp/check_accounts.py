import frappe

def execute():
    # Check existing Payroll Entries
    pes = frappe.get_all("Payroll Entry", fields=["name", "currency", "exchange_rate", "payroll_payable_account", "payment_account", "company"])
    print(f"Payroll Entries: {len(pes)}")
    for p in pes:
        print(f"  {p.name} | cur={p.currency} | ex={p.exchange_rate} | payable={p.payroll_payable_account} | pay_acct={p.payment_account} | co={p.company}")

    # Check Chart of Accounts for payroll
    accounts = frappe.get_all("Account",
        filters={"company": "الشاحذي", "account_type": ["in", ["Payroll", "Payable"]]},
        fields=["name", "account_type", "root_type"],
    )
    print(f"\nPayroll/Payable accounts:")
    for a in accounts:
        print(f"  {a.name} ({a.account_type}) root={a.root_type}")

    # Check all liability accounts
    liab = frappe.get_all("Account",
        filters={"company": "الشاحذي", "root_type": "Liability"},
        fields=["name", "account_type"],
    )
    print(f"\nLiability accounts:")
    for a in liab:
        print(f"  {a.name} ({a.account_type})")

    # Check all expense accounts
    exp = frappe.get_all("Account",
        filters={"company": "الشاحذي", "root_type": "Expense"},
        fields=["name", "account_type"],
    )
    print(f"\nExpense accounts:")
    for a in exp:
        print(f"  {a.name} ({a.account_type})")

    # Check Cash accounts
    cash = frappe.get_all("Account",
        filters={"company": "الشاحذي", "account_type": "Cash"},
        fields=["name", "account_type"],
    )
    print(f"\nCash accounts:")
    for a in cash:
        print(f"  {a.name}")

    # Check if YER currency exchange rate is set
    er = frappe.db.sql("SELECT name, exchange_rate FROM `tabCurrency Exchange` WHERE currency='YER'", as_dict=True)
    print(f"\nYER Exchange Rates: {er}")
