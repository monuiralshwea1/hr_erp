# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	conversation = filters.get("conversation")
	columns = [
	    {
	        "label": _("Message Id"),
	        "fieldname": "Message Id",
	        "fieldtype": "Link",
	        "options": "Internal Message",
	        "width": 150
	    },
	    {
	        "label": _("Created On"),
	        "fieldname": "Created On",
	        "fieldtype": "Date",
	        "width": 160
	    },
	    {
	        "label": _("Created At"),
	        "fieldname": "Created At",
	        "fieldtype": "Data",
	        "width": 160
	    },
	    {
	        "label": _("Subject"),
	        "fieldname": "Subject",
	        "fieldtype": "Data",
	        "width": 300
	    },
	    {
	        "label": _("Sender Department"),
	        "fieldname": "Sender Department",
	        "fieldtype": "Data",
	        "width": 180
	    },
	    {
	        "label": _("Sender Employee"),
	        "fieldname": "Sender Employee",
	        "fieldtype": "Data",
	        "width": 180
	    },
	    {
	        "label": _("Status"),
	        "fieldname": "Status",
	        "fieldtype": "Data",
	        "width": 120
	    }
	]


	fetch_data = frappe.db.sql(f"""
	    SELECT 
	        msg.name AS 'Message Id',
	        DATE(msg.issue_date) AS 'Created On',
	        DATE_FORMAT(msg.issue_date, '%r') AS 'Created At',
	        msg.subject AS 'Subject',
	        REPLACE(dep.department_name, ' - SH', '') AS 'Sender Department',
	        msg.employee_name AS 'Sender Employee',
	        msg.message_status AS 'Status',
	        GROUP_CONCAT(CONCAT(td.employee_name, ' (', REPLACE(to_dep.department_name, ' - SH', ''), ')') SEPARATOR ' | ') AS "To"
	    FROM 
	        `tabInternal Message` AS msg
	    LEFT JOIN 
	        `tabInternal Message` AS root
	        ON root.name = msg.conversation_id
	    LEFT JOIN 
	        `tabEmployees List` AS td
	        ON td.parent = msg.name
	    LEFT JOIN 
	        `tabDepartment` AS dep
	        ON dep.name = msg.from_department 
	    LEFT JOIN 
	        `tabDepartment` AS to_dep
	        ON to_dep.name = td.department
	    WHERE 
	        msg.conversation_id = '{conversation}' OR msg.name = '{conversation}'
	    GROUP BY 
	        msg.name
	    ORDER BY 
	        msg.creation ASC
	""", as_dict=True)

	max_cols = 0

	for msg in fetch_data:
	    to_list = [t.strip() for t in msg.To.split(" | ")]
	    if len(to_list) > max_cols:
	        max_cols = len(to_list)
        
	for col in range(0,max_cols):
	    columns.append(
	    {
	        "label": _(f"To"),
	        "fieldname": f"To({col})",
	        "fieldtype": "Data",
	    })

	final_data = []
	for msg in fetch_data:

	    row = {
	        "Message Id": msg["Message Id"],
	        "Created On": msg["Created On"],
	        "Created At": msg["Created At"],
	        "Subject": msg["Subject"],
	        "Sender Department": msg["Sender Department"],
	        "Sender Employee": msg["Sender Employee"],
	        "Status": msg["Status"]
	    }

	    receiver_list = [r.strip() for r in msg.To.split(" | ") if r.strip()]
	    receiver_index = 0
	    for receiver in receiver_list:
	        row[f"To({receiver_index})"] = receiver
	        receiver_index = receiver_index + 1

	    final_data.append(row)
	return columns, final_data
