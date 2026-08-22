frappe.provide("hr_erp.employee_autofill");

hr_erp.employee_autofill.fetch_employee = function(emp, callback) {
    if (!emp) { callback({}); return; }
    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Employee",
            filters: { name: emp },
            fieldname: ["employee_name", "department", "designation", "branch", "company", "default_shift"]
        },
        callback: function(r) { callback(r && r.message ? r.message : {}); }
    });
};

hr_erp.employee_autofill.apply_to_fields = function(frm, d, fieldnames) {
    fieldnames.forEach(function(fn) {
        if (frm.fields_dict[fn]) frm.set_value(fn, d[fn] || "");
    });
};

hr_erp.employee_autofill.apply_to_row = function(grid_row, d) {
    ["employee_name", "department", "designation", "default_shift", "branch"].forEach(function(fn) {
        if (grid_row.fields_dict[fn]) grid_row.fields_dict[fn].set_value(d[fn] || "");
    });
};

// Auto-setup main form
hr_erp.employee_autofill.setup = function(frm) {
    if (!frm || frm._emp_af_done) return;
    var emp_field = null;
    (frm.meta.fields || []).forEach(function(f) {
        if (f.fieldname === "employee" && f.fieldtype === "Link" && f.options === "Employee") emp_field = f;
    });
    if (!emp_field) return;
    frm._emp_af_done = true;

    frm.on("employee", function(frm) {
        if (!frm.doc.employee) {
            ["employee_name", "department", "designation", "branch", "default_shift"].forEach(function(fn) {
                if (frm.fields_dict[fn]) frm.set_value(fn, "");
            });
            return;
        }
        hr_erp.employee_autofill.fetch_employee(frm.doc.employee, function(d) {
            hr_erp.employee_autofill.apply_to_fields(frm, d, ["employee_name", "department", "designation", "branch", "default_shift"]);
            if (frm.fields_dict["company"] && !frm.doc.company) frm.set_value("company", d.company || "");
        });
    });
};

// Auto-setup child tables with employee field
hr_erp.employee_autofill.setup_child_tables = function(frm) {
    if (!frm || frm._emp_af_child_done) return;
    frm._emp_af_child_done = true;

    (frm.meta.fields || []).forEach(function(f) {
        if (f.fieldtype === "Table" && f.options) {
            var child_meta = frappe.get_meta(f.options);
            if (!child_meta) return;
            var has_emp = false;
            (child_meta.fields || []).forEach(function(cf) {
                if (cf.fieldname === "employee" && cf.fieldtype === "Link" && cf.options === "Employee") has_emp = true;
            });
            if (!has_emp) return;

            var grid = frm.fields_dict[f.fieldname];
            if (!grid || !grid.grid) return;

            grid.grid.wrapper.on("grid-row-refresh", function(event, grid_row) {
                var row = grid_row.doc;
                if (!row || row._emp_af_row) return;
                row._emp_af_row = true;

                var emp_input = grid_row.fields_dict["employee"] && grid_row.fields_dict["employee"].$input;
                if (emp_input) {
                    emp_input.on("change", function() {
                        var emp = row.employee;
                        if (!emp) {
                            ["employee_name", "department", "designation", "default_shift"].forEach(function(fn) {
                                if (grid_row.fields_dict[fn]) grid_row.fields_dict[fn].set_value("");
                            });
                            return;
                        }
                        hr_erp.employee_autofill.fetch_employee(emp, function(d) {
                            hr_erp.employee_autofill.apply_to_row(grid_row, d);
                            frm.dirty();
                        });
                    });
                }
            });
        }
    });
};

$(document).on("form-refresh", function(e, frm) {
    hr_erp.employee_autofill.setup(frm);
    hr_erp.employee_autofill.setup_child_tables(frm);
});
