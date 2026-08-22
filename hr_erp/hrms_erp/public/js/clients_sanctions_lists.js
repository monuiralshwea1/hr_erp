frappe.ui.form.on('Clients Sanctions Lists', {
    refresh: function(frm) {
        

        
        if(frm.doc.workflow_state == "Waiting")
        {
            if(frm.doc.retrieve_reason)
            {
                frm.dashboard.set_headline_alert();
                frm.dashboard.set_headline_alert(
                    frm.doc.retrieve_reason, 
                    'red'
                );
            }
            
           
            frm.disable_save();
        }
    },
    
    client_id: function(frm) {
        show_fetch_button(frm);
    },
    test_result: function(frm) {
        show_fetch_button(frm);
    },
    review_description: function(frm) {
        show_fetch_button(frm);
    },
    before_workflow_action:  async function(frm) {
        if (frm.selected_workflow_action === 'Reviewed')
        {
            return new Promise((resolve) => {
                frm.set_value('retrieve_reason', ");
                frm.save().then(() => {
                    resolve();
                });
            });
        }
        else if (frm.selected_workflow_action === 'Retrieve') {
            frappe.dom.unfreeze();
            return new Promise((resolve, reject) => {
                let dialog = new frappe.ui.Dialog({
                    title: __('Enter Retrieval Reason'),
                    fields: [
                        {
                            label: __('Reason for Retrieval'),
                            fieldname: 'retrieve_reason',
                            fieldtype: 'Small Text',
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Submit'),
                    primary_action(values) {
                        frm.set_value('retrieve_reason', values.retrieve_reason);
                        frm.set_value('description', values.retrieve_reason + "\n" + frm.doc.description);
                        frm.set_df_property('description', 'reqd', 0);
                        dialog.hide();
                        frm.save().then(() => {
                            resolve();
                        });
                    }
                });
                
                dialog.on_cancel = () => {
                    reject();
                };
                
                dialog.show();
            });
        }
        frm.reload_doc();
    }
});


function show_fetch_button(frm)
{
    if(frm.doc.workflow_state == "Waiting")
    {
        frm.disable_save();
        frappe.dom.set_style(`
            .btn-white-text, .btn-white-text:hover, .btn-white-text:focus, .btn-white-text:active {
                color: #ffffff !important;
            }
        `);
        
        frm.add_custom_button(__('Fetch Client Data'), function() {
            frm.save();
            
        }).addClass('btn-primary btn-white-text');
    }
}