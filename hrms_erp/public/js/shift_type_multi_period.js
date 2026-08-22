// Copyright (c) 2026, Shumul. All rights reserved.
// Client Script for Multi-Period Shift Management on Shift Type form

frappe.ui.form.on("Shift Type", {
	refresh(frm) {
		if (frm.doc.enable_multi_period && !frm.doc.__islocal) {
			calculate_period_summary(frm);
			frm.add_custom_button(__("Preview Attendance"), () => {
				preview_multi_period_attendance(frm);
			}, __("Tools"));
		}
	},

	enable_multi_period(frm) {
		if (frm.doc.enable_multi_period) {
			frm.toggle_display("attendance_day_start_time", true);
			frm.toggle_display("shift_periods", true);
			if (!frm.doc.attendance_day_start_time) {
				frm.set_value("attendance_day_start_time", "06:00:00");
			}
		}
	},

	shift_periods(frm) {
		if (frm.doc.enable_multi_period) {
			validate_period_overlaps(frm);
			calculate_period_summary(frm);
		}
	},
});

frappe.ui.form.on("Shift Period", {
	start_time(frm, cdt, cdn) {
		validate_period_overlaps(frm);
		calculate_period_summary(frm);
	},

	end_time(frm, cdt, cdn) {
		validate_period_overlaps(frm);
		calculate_period_summary(frm);
	},

	is_break(frm, cdt, cdn) {
		calculate_period_summary(frm);
	},

	allow_overtime(frm, cdt, cdn) {
		calculate_period_summary(frm);
	},

	period_number(frm, cdt, cdn) {
		validate_period_overlaps(frm);
	},
});

function validate_period_overlaps(frm) {
	if (!frm.doc.shift_periods || frm.doc.shift_periods.length < 2) return;

	const periods = frm.doc.shift_periods.filter(p => !p.is_break);
	for (let i = 0; i < periods.length; i++) {
		for (let j = i + 1; j < periods.length; j++) {
			const a = periods[i];
			const b = periods[j];
			if (a.start_time && a.end_time && b.start_time && b.end_time) {
				if (time_to_minutes(a.start_time) < time_to_minutes(b.end_time) &&
					time_to_minutes(b.start_time) < time_to_minutes(a.end_time)) {
					frappe.msgprint({
						title: __("Overlap Detected"),
						message: __("Period '{0}' overlaps with period '{1}'").format(a.period_name, b.period_name),
						indicator: "red"
					});
					return;
				}
			}
		}
	}
}

function calculate_period_summary(frm) {
	if (!frm.doc.shift_periods) return;

	let totalWorking = 0;
	let totalBreak = 0;

	frm.doc.shift_periods.forEach(p => {
		if (p.start_time && p.end_time) {
			const mins = time_diff_minutes(p.start_time, p.end_time);
			if (p.is_break) {
				totalBreak += mins;
			} else {
				totalWorking += mins;
			}
		}
	});

	frm.set_value("total_working_period_hours", Math.round((totalWorking / 60) * 100) / 100);
	frm.set_value("total_break_period_hours", Math.round((totalBreak / 60) * 100) / 100);
}

function time_to_minutes(t) {
	if (!t) return 0;
	const parts = t.split(":");
	return parseInt(parts[0]) * 60 + parseInt(parts[1]) + (parts[2] ? parseInt(parts[2]) / 60 : 0);
}

function time_diff_minutes(t1, t2) {
	return time_to_minutes(t2) - time_to_minutes(t1);
}

function preview_multi_period_attendance(frm) {
	frappe.msgprint({
		title: __("Multi-Period Shift Preview"),
		message: frm.doc.shift_periods.map(p =>
			`<b>${p.period_name}</b> (${p.period_number}): ${p.start_time} → ${p.end_time} ${p.is_break ? '☕ ' + __("Break") : ''}`
		).join("<br>"),
		indicator: "green"
	});
}
