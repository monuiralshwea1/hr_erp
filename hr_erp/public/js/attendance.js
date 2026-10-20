// hr_erp: Attendance client enhancements
// ---------------------------------------------------------------------------
// تعبئة تلقائية لفترات نوبة العمل في نموذج التحضير اليدوي:
//   - عند اختيار الموظف (أو الشفت/التاريخ) تُجلب فترات الشفت وتُعبَّأ في جدول
//     "🔄 فترات نوبة العمل" (attendance_period_details).
//   - لكل فترة خانة "حاضر" (present) قابلة للتعديل؛ فإذا أُلغي تحديد فترة
//     (أو حُذف صفها) تُستنتج الحالة تلقائياً: حاضر / نصف يوم / غائب.
//   - فترات الراحة (is_break) لا تؤثر في تحديد الحالة.
// ---------------------------------------------------------------------------

frappe.ui.form.on("Attendance", {
	onload(frm) {
		if (!frm.doc.attendance_date) {
			frm.set_value("attendance_date", frappe.datetime.get_today());
		}
	},

	refresh(frm) {
		if (!frm.is_new()) {
			return;
		}

		frm.add_custom_button(
			__("تعبئة فترات النوبة"),
			() => populate_periods(frm, { force: true, notify: true }),
			__("إجراء")
		);

		frm.add_custom_button(
			__("حاضر"),
			() => {
				frm.set_value("status", "Present");
				frm.set_value("half_shifts", 0);
				set_all_periods_present(frm, true);
			},
			__("إجراء")
		);

		frm.add_custom_button(
			__("غائب"),
			() => {
				frm.set_value("status", "Absent");
				frm.set_value("half_shifts", 0);
				set_all_periods_present(frm, false);
			},
			__("إجراء")
		);

		// تعبئة أولية عند فتح النموذج إن كانت البيانات متوفرة (مثلاً فتح بالانتقال).
		setTimeout(() => populate_periods(frm), 300);
	},

	employee(frm) {
		if (!frm.doc.employee) {
			return;
		}
		frappe.call({
			method: "hr_erp.hrms_erp.multi_period_shift.api.get_employee_default_shift",
			args: { employee: frm.doc.employee },
			callback: (r) => {
				if (r.message && r.message !== frm.doc.shift) {
					frm.set_value("shift", r.message);
				} else {
					populate_periods(frm);
				}
			},
		});
	},

	shift(frm) {
		populate_periods(frm, { notify: true });
	},

	attendance_date(frm) {
		populate_periods(frm);
	},
});

frappe.ui.form.on("Attendance Period Detail", {
	present(frm) {
		set_status_from_periods(frm);
	},
	attendance_period_details_add(frm) {
		set_status_from_periods(frm);
	},
	attendance_period_details_remove(frm) {
		set_status_from_periods(frm);
	},
});

function populate_periods(frm, opts) {
	opts = opts || {};

	if (!frm.doc.shift || !frm.doc.attendance_date) {
		if (opts.notify) {
			frappe.show_alert({ message: __("اختر الموظف والشفت والتاريخ أولاً."), indicator: "orange" });
		}
		return;
	}
	if (!frm.doc.employee) {
		frappe.show_alert({ message: __("اختر الموظف أولاً."), indicator: "orange" });
		return;
	}

	// لا نستبدل الصفوف في سجل محفوظ إلا عند الطلب الصريح.
	const has_rows = (frm.doc.attendance_period_details || []).length > 0;
	if (has_rows && !opts.force) {
		return;
	}

	frappe.call({
		method: "hr_erp.hrms_erp.multi_period_shift.api.get_shift_period_details",
		args: {
			shift_type: frm.doc.shift,
			date: frm.doc.attendance_date,
			employee: frm.doc.employee,
		},
		callback: (r) => {
			const data = r.message || {};
			if (!data.multi_period || !(data.periods || []).length) {
				if (opts.notify) {
					frappe.show_alert({
						message: __("الشفت «{0}» غير مُهيّأ لفترات متعددة.", [frm.doc.shift]),
						indicator: "orange",
					});
				}
				return;
			}

			frm.clear_table("attendance_period_details");
			(data.periods || []).forEach((p) => {
				frm.add_child("attendance_period_details", {
					employee: frm.doc.employee,
					shift_type: frm.doc.shift,
					period_name: p.period_name,
					period_number: p.period_number,
					period_start: p.period_start,
					period_end: p.period_end,
					present: p.is_break ? 0 : 1,
					is_break: p.is_break ? 1 : 0,
					period_status: p.is_break ? "Break" : "Present",
				});
			});
			frm.set_value("period_entry_manual", 1);
			frm.refresh_field("attendance_period_details");
			set_status_from_periods(frm);
		},
	});
}

function set_status_from_periods(frm) {
	const rows = frm.doc.attendance_period_details || [];
	const work = rows.filter((r) => !r.is_break);

	if (!work.length) {
		return;
	}

	const present_count = work.filter((r) => to_int(r.present)).length;
	const total = work.length;

	let status = "Present";
	if (present_count === 0) {
		status = "Absent";
	} else if (present_count < total) {
		status = "Half Day";
	}

	// ساعات العمل = مجموع ساعات الفترات الحاضرة.
	let working_hours = 0;
	work.forEach((r) => {
		if (to_int(r.present)) {
			working_hours += period_hours(r.period_start, r.period_end);
		}
		r.period_status = to_int(r.present) ? "Present" : "Absent";
	});

	frm.set_value("status", status);
	frm.set_value("half_shifts", status === "Half Day" ? 1 : 0);
	frm.set_value("working_hours", Math.round(working_hours * 100) / 100);

	frm.refresh_field("attendance_period_details");
}

function set_all_periods_present(frm, value) {
	(frm.doc.attendance_period_details || []).forEach((r) => {
		if (!r.is_break) {
			r.present = value ? 1 : 0;
		}
	});
	frm.refresh_field("attendance_period_details");
	set_status_from_periods(frm);
}

function period_hours(start, end) {
	if (!start || !end) {
		return 0;
	}
	const s = frappe.datetime.str_to_obj(start);
	const e = frappe.datetime.str_to_obj(end);
	const diff = (e - s) / 1000 / 3600;
	return diff > 0 ? diff : 0;
}

function to_int(value) {
	return parseInt(value || 0, 10) || 0;
}
