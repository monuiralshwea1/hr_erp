frappe.query_reports["Shift Summary V2"] = {
    "formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if(value == "-")
            value = "<div style='background-color:grey;color:white;text-align:center;'>-</div>";
		else if (value == "" || value == undefined) {
			value = "<div style='background-color:red;color:white;text-align:center;'>لايوجد</div>";
		}
		return value;
	},
};