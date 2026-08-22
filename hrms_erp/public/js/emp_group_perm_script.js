// Replace 'Your Parent DocType Name' with the actual name of your parent DocType
// Replace 'employee_group' with the fieldname of your Employee Group link field in the parent
// Replace 'selected_employees' with the fieldname of your Child Table field in the parent
// Replace 'employee' with the fieldname of the Employee link field INSIDE your Child DocType

frappe.ui.form.on('User Group Permissions', {
    // --- 1. Trigger filtering when the form loads or refreshes ---
    refresh: function(frm) {
        // Apply the filter initially if an employee_group is already selected
        if (frm.doc.employee_group) {
            set_employee_query_for_group(frm);
        } else {
            // Optional: Clear filter if no group is selected on load
            clear_employee_query(frm);
        }
    },

    // --- 2. Trigger filtering when the 'employee_group' field changes ---
    employee_group: function(frm) {
        // Clear the child table when the group changes? Recommended.
        // You might want to confirm this with the user first in a real scenario.
        frm.set_value('selected_employees', []); // Clears the table

        if (frm.doc.employee_group) {
            // Set the new filter based on the selected group
            set_employee_query_for_group(frm);
        } else {
            // If group is cleared, remove the filter
            clear_employee_query(frm);
        }
        // Refresh the table field visually
        frm.refresh_field('selected_employees');
    }
});

// --- Helper function to set the query ---
function set_employee_query_for_group(frm) {
    var child_table_fieldname = 'selected_employees'; // Your child table fieldname in parent
    var employee_link_fieldname = 'employee';         // Your employee link fieldname in child

    // This tells the system how to filter the 'employee' field within the 'selected_employees' table
    frm.set_query(employee_link_fieldname, child_table_fieldname, function(doc, cdt, cdn) {
        // doc: parent document object
        // cdt: child document type (e.g., 'Group Employee Link')
        // cdn: child document name (unique row ID)

        return {
            filters: {
                // Filter Employee doctype where 'employee_group' matches the parent's selection
                'employee_group': frm.doc.employee_group,
                // It's good practice to only show active employees
                'status': 'Active'
            }
        };
    });
}

// --- Helper function to clear/reset the query ---
function clear_employee_query(frm) {
    var child_table_fieldname = 'selected_employees'; // Your child table fieldname in parent
    var employee_link_fieldname = 'employee';         // Your employee link fieldname in child

    // Set a less restrictive query (e.g., only active employees) or remove specific filters
    frm.set_query(employee_link_fieldname, child_table_fieldname, function() {
        return {
            filters: {
                 'status': 'Active' // Still filter by active status, but no group filter
            }
            // Or return {} for no filters at all, though filtering by Active is usually desired.
        };
    });
}