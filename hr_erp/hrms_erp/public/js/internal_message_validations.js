frappe.ui.form.on('Internal Message', {
    onload: function(frm){
        hide_sidebar(frm);
        
        get_user_details(frm);

        // get_user_details(frm);
    },
    after_save: function(frm)
    {
        const el = document.getElementById("alert-container");
        if(el != undefined)
            el.style.display = "none";
    },
    to_employees: function(frm){
        cur_frm.doc.to_employees.remove
    },
    before_save: function(frm){
      console.log("before_save");  
    },
    validate: function(frm){
        const employees = frm.doc.to_employees || [];
        const seen = new Set();
        for (let i = 0; i < employees.length; i++) {
          const emp = employees[i].employee;
             console.log(emp, emp == frm.doc.issued_by_emp)
          if (!emp) continue;
            
          if (seen.has(emp) || emp == frm.doc.issued_by_emp) {
            // Duplicate found — remove this row
            console.log('🧹 Removing duplicate at index', i, 'Employee:', emp);
    
            employees.splice(i, 1); // remove one element at index i
            i--; // adjust index because the array just shrank
          } else {
            seen.add(emp);
          }
        }
        console.log(employees);
        frm.refresh_field('to_employees');
    },
    in_team_name: function(frm){
        is_team_name_required(frm, frm.doc.in_team_name);
    },
	refresh(frm) {
        // ggg(frm);
        hide_sidebar(frm);
        add_quick_inbox_list_buttons(frm);
        
	    show_action_buttons(frm);
	    control_buttons_visiblity(frm);
	    is_team_name_required(frm, frm.doc.in_team_name);
	},
})

// async function ggg(frm){
//   const employees = await frappe.db.get_list('Employee', {
//         fields: ['name', 'department', "is_manager"],  // Get all fields (use with caution)
//         filters:[
//         ],
//         limit:0,
//     });
    
//     console.log(employees);
// }
function is_team_name_required(frm, req)
{
    frm.set_df_property("custom_team_name", "reqd", req);
}
function enable_editing(frm, read_only){
    frm.set_df_property("description", "read_only", read_only);
    frm.set_df_property("subject", "read_only", read_only);
    frm.set_df_property("to_employees", "read_only", read_only);
    frm.set_df_property("attachments", "read_only", read_only);
    frm.set_df_property("in_team_name", "read_only", read_only);
    frm.set_df_property("custom_team_name", "read_only", read_only);
}

function control_buttons_visiblity(frm){
   const btn = cur_frm.page.btn_primary && cur_frm.page.btn_primary[0];
    if (!btn) return;
    if(cur_frm.page.btn_primary[0].innerText == "اعتماد"  || cur_frm.page.btn_primary[0].innerText == "Submit"){
        cur_frm.page.btn_primary.hide()
    }else
    {
        cur_frm.page.btn_primary.show()
    }
    
    const observer = new MutationObserver(() => {
        
        const newText = btn.innerText.trim();
        if(newText == "اعتماد" |newText == "Submit"){
            cur_frm.page.btn_primary.hide()
        }else
        {
            cur_frm.page.btn_primary.show()
        }
    });

    observer.observe(btn, { childList: true, characterData: true, subtree: true });
  
    if(!frm.is_new())
    {
	    cur_frm.page.btn_secondary.hide()
    }
}

frappe.ui.form.on('Employees List', {
    employee: async function(frm, cdt, cdn) {
        await cur_frm.trigger("validate");
        cur_frm.refresh_field('to_employees');
        
        
        
        if(frm.doc.docstatus == 1)
            frm.save('Update');
        // else
        //     frm.save();
    },
    add_employee: function(frm){
    }
})

function check_mandatory_fields(frm) {
  const missing_fields = [];

  // Loop through all fields in the form
  frm.meta.fields.forEach(df => {
    // Skip non-mandatory fields
    if (!df.reqd) return;

    // Get field value
    const value = frm.doc[df.fieldname];

    // Handle empty values (different datatypes)
    if (
      value === undefined ||
      value === null ||
      value === " ||
      (Array.isArray(value) && value.length === 0)
    ) {
      missing_fields.push(df.label);
    }
  });

  // If missing fields, show validation message
  if (missing_fields.length > 0) {
    const msg = __('⚠️ يرجى ملء الحقول الإلزامية التالية قبل المتابعة:') +
      '<br><ul>' + missing_fields.map(f => `<li>${f}</li>`).join('') + '</ul>';
    frappe.throw(msg);
  } else {
    frappe.msgprint(__('✅ جميع الحقول الإلزامية ممتلئة.'));
  }
}

async function show_action_buttons(frm){
    var can_send = true;
    var can_retreive = false;
        
    if(frm.doc.docstatus == 1)
    {
        goto_conversion_report(frm);
        
        
        await frappe.call({
            method: 'validate_message',
            args:{
                // to_employees: frm.doc.to_employees,
                name: frm.doc.name
            },
            callback: function(r) {
                can_send = r.can_send;
                can_retreive = r.can_retreive;
                
            }
        });
        
        if(can_retreive)
        {
            var btn_retrieve = frm.add_custom_button("Retrieve Message", async function() {
                await retrive(frm);
    	    });
    	    
    	    btn_retrieve.css({
                'background-color': '#dd2424',  // blue
                'color': 'white',
                'border-radius': '8px',
                'font-weight': 'bold'
            });
        }
    }
    if(!frm.is_new())
    {
        if(frm.doc.docstatus == 0 || frm.doc.docstatus == 1){
            if(can_send){
                var btn_send = frm.add_custom_button("Send", async function() {
                    await send_message(frm);
        	    });
        	    
        	    btn_send.css({
                    'background-color': '#28c966',  // blue
                    'color': 'white',
                    'border-radius': '8px',
                    'font-weight': 'bold'
                });
            }
            
        }

    }
    if(!frm.is_new())
    {
        var btn_delete = frm.add_custom_button("Delete", async function() {
            await message_delete(frm);
	    });
	    
	    btn_delete.css({
            'background-color': 'red',  // blue
            'color': 'white',
            'border-radius': '8px',
            'font-weight': 'bold'
        });
    }
    
    enable_editing(frm, !can_send || frm.doc.docstatus == 2);
}

function goto_conversion_report(frm){
    frm.add_custom_button('View Conversation', function() {
            if (frm.doc.name) {
                
                var urlValue = frm.doc.conversation_id == undefined ? frm.doc.name : frm.doc.conversation_id;
                
                const report_url = `/app/query-report/Conversation%20Replies%20Report?conversation=${urlValue}`;
                window.open(report_url, '_blank'); // open in new tab
            } else {
                frappe.msgprint('Please save the document first.');
            }
        }); // Optional group name for button
}


async function message_delete(frm)
{
    frappe.confirm(
    "هل تريد تأكيد حذف الرسالة؟",
    await function() {
         frappe.call({
            method: 'delete_internal_message',
            args: {
                name: frm.doc.name
            },
            callback: function(r) {
                if (!r.exc) {
                    frappe.show_alert({ message: __('Document Cancelled'), indicator: 'green' });
                    frappe.set_route('List', frm.doc.doctype)
                }
            }
        });
    },
    function() {}
    )
     
}
async function retrive(frm)
{
    await frappe.call({
        method: 'cancel_linked_inbox',
        args:{
            docstatus : 0,
            internal_reference_id: frm.doc.name,
        },
        callback: function(r) {
            // if (!r.exc) {
            //     frappe.msgprint('Document cancelled successfully.');
            //     frm.reload_doc();
            // }
            frm.reload_doc();
        }
    });
    
}
async function send_message(frm)
{
    await frappe.call({
        method: 'send_message',
        args:{
            // to_employees: frm.doc.to_employees,
            // from_department: frm.doc.from_department,
            // from_employee_name: frm.doc.employee_name,
            // from_employee: frm.doc.issued_by_emp,
            // issue_date: frm.doc.issue_date,
            // subject: frm.doc.subject,
            // attachments: frm.doc.attachments,
            // description: frm.doc.description,
            // internal_reference_id: frm.doc.internal_reference_id,
            // conversation_id: frm.doc.conversation_id,
            name: frm.doc.name
        },
        callback: function(r) {
            // if (!r.exc) {
            //     frappe.msgprint('Document cancelled successfully.');
            //     frm.reload_doc();
            // }
            var docs = r.inboxDocs;
            console.log(docs);
            for(var doc of docs){
                
                var user_id = frm.doc.to_employees.filter(x => x.employee == doc.employee)[0].user_id;
                doc["user_id"] = user_id;
            }
            
            notify_users(frm, docs);
            frm.reload_doc();
            
        }
    });
    
}


async function notify_users(frm, docs){
    
    console.log("notify_users");
    await frappe.call({
        method: 'send_notification',
        args:{
            docs: docs,
            subject: `وصول رسالة جديدة إلى صندوق الوارد: ${frm.doc.subject}`,
            message: `<p>تم استلام رسالة جديدة من ${ frm.doc.employee_name} بخصوص ${ frm.doc.subject }.</p>`,
            doctype: "Inbox Messages",
        },
        callback: function(r) {
            
        }
    });
}

async function get_employees_list(frm, in_inbox_managers_list)
{
    if(in_inbox_managers_list)
    {
        var managers_list = []
        await frappe.call({
            method: 'get_employees_internal_message',
            args:{
                department: frm.doc.from_department,
            },
            callback: function(r) {
                managers_list = r.results;
            }
        });
        
        const employeeNames = managers_list.map(e => e.name);
        
        frm.fields_dict['to_employees'].grid.get_field('employee').get_query = function(doc, cdt, cdn) {
             return {
                filters: [
                    ["name", "in", employeeNames]
                ]
            };
        };
    }else
    {
         frm.fields_dict['to_employees'].grid.get_field('employee').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    department: doc.from_department,   // filters by department field in parent form
                    status: 'Active'              // filter only active employees
                }
            };
        };
    }

}

async function get_user_details(frm)
{
     const employees = await frappe.db.get_list('Employee', {
            fields: ['name', 'department', "is_manager", "in_inbox_managers_list"],  // Get all fields (use with caution)
            filters:[
                ["status", "=", "Active"],
                ["user_id", "=", frappe.session.user]
            ],
            limit:0,
        });
    if(cur_frm.is_new())
    {
        frm.set_value('issued_by_user', frappe.session.user);
        frm.set_value('issued_by_emp', employees[0].name);
        frm.set_value('from_department', employees[0].department);
    }
    console.log(employees);
    if(employees && employees.length > 0)
        get_employees_list(frm, employees[0].in_inbox_managers_list);
}

function add_quick_inbox_list_buttons(frm)
{
    
    const targetDiv = document.getElementsByClassName("form-sidebar overlay-sidebar hidden-xs hidden-sm")[0].parentElement;
    if (targetDiv) {
        // Check if the button already exists
        if (!targetDiv.querySelector("#inbox-button")) {
            const btn = document.createElement("button");
            btn.id = "inbox-button"; // unique ID to prevent duplication
            btn.textContent = "عرض قائمة الوارد";
            btn.className = "btn btn-default ellipsis w-100"; // Frappe/Bootstrap style
            btn.onclick = () => {
                const report_url = `/app/inbox-messages`;
                window.open(report_url, "_blank"); // open in new tab
            };
            targetDiv.appendChild(btn);
        }
    }
}

function hide_sidebar(frm){
    var element = document.getElementsByClassName("form-sidebar");
    element[0].hidden = true;
}