frappe.query_reports["Biometric Period Attendance"] = {
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "status" || column.fieldname === "period_status") {
			var bg = {
				"حاضر": "#39ed39",
				"غائب": "#ff4d4d",
				"متأخر": "#ffae00",
				"نصف يوم": "#ffae00",
				"في إجازة": "#00c4ff",
				"إجازة": "#00c4ff",
				"عطلة رسمية": "#6cafb1",
				"عمل من المنزل": "#00d3ff",
				"استراحة": "#d3d3d3",
			};
			var color = bg[value];
			if (color) {
				value = "<div style='background-color:" + color + ";color:white;text-align:center;padding:2px;'>" + value + "</div>";
			}
		}
		return value;
	},
};