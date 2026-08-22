frappe.ui.form.on('Long Term Advance', {
	 refresh: function(frm) {

        // if (frm.doc.docstatus === 0) {
        //     frm.add_custom_button(__('Calculate Advances'), function() {
        //         // Your button action here
        //         calculate_advance(frm)
        //     });
        // }
      
    },
})

frappe.ui.form.on('Long Term Advance Table', {
 	months: function(frm, cdt, cdn) {

        calculate_advance_change(frm, cdt, cdn);
	},
	value: function(frm, cdt, cdn) {

        calculate_advance_change(frm, cdt, cdn);
	},
})


function calculate_advance_change(frm, cdt, cdn){
    let changed_row = frappe.get_doc(cdt, cdn); 

    changed_row.value_per_month = changed_row.value / changed_row.months;

    frm.refresh_field("advance_list");
}

// function calculate_advance(frm){
//     if (!frm.doc.title) {
//         frappe.msgprint(__('Please fill all mandatory data.'));
//         return;
//     }
    
//     frappe.show_alert({message: __('Calculating...'), indicator: 'green'});
//     frm.doc.advance_list = [];
//     let current_date = new Date(frm.doc.from_date);
    
//     let monthly_amount = frm.doc.amount / frm.doc.months;
    
//     for(let i = 0; i < frm.doc.months; i++){
//         let current_fromatted_date = moment(current_date).format('YYYY-MM-DD');

//         let row = {
//             doctype: "Long Term Advance Table",
//             employee: frm.doc.employee,
//             date: current_fromatted_date,
//             value: monthly_amount,
//         };
//         frm.add_child("advance_list", row);
        
//         current_date.setMonth(current_date.getMonth() + 1);
//     }
//     frm.refresh_field("advance_list");

// }