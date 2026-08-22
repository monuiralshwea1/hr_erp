frappe.query_reports["Attendance Summary V2"] = {
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (value == "L") {
			value = "<div style='background-color:#00c4ff;color:white;text-align:center;'>" + value + "</div>";
		}
		else if (value == "A") {
			value = "<div style='background-color:red;color:white;text-align:center;'>" + value + "</div>";
		}
		else if (value.toString().includes("P in") || value.toString().includes("P out")) {
			value = "<div style='background-color:#28a24e;color:white;text-align:center;'>" + value + "</div>";
		}
		else if (value == "P") {
			value = "<div style='background-color:#39ed39;color:white;text-align:center;'>" + value + "</div>";
		}
		else if (value == "HD") {
			value = "<div style='background-color:#ffae00;color:white;text-align:center;'>" + value + "</div>";
		}
		else if (value == "W") {
			value = "<div style='background-color:#00d3ff;color:white;text-align:center;'>" + value + "</div>";
		}
		else if (value == "H") {
			value = "<div style='background-color:#6cafb1;color:white;text-align:center;'>" + value + "</div>";
		}
		return value;
	},
};