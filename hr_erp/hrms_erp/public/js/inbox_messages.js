frappe.ui.form.on('Inbox Messages', {
	refresh(frm) {
	    hide_sidebar(frm);
        add_quick_outbox_list_buttons(frm);
		add_quick_outbox_buttons(frm);
		goto_conversion_report(frm);
		if(frm.doc.docstatus == 1)
		{
		    frm.add_custom_button("Reply On Message", function() {
                frappe.new_doc("Internal Message", {}, 
                    doc=>{
                        doc.subject = frm.doc.subject;
                        const reply = get_reply_message(frm);
                        doc.description = reply;
                        doc.inbox_reference_id = frm.doc.name;
                        doc.reference_id = frm.doc.internal_reference_id;
                        doc.message_status = "Reply";
                        doc.conversation_id = frm.doc.conversation_id;
                        
                        //Copy attachements
                        doc.attachments = [];
                        for (let i = 0; i < frm.doc.attachments.length; i++) {
                            let row = frappe.model.add_child(doc, "attachments");
                            // console.log(frm.doc.attachments[i]);
                            row.attachment = frm.doc.attachments[i].attachment;
                        }
                        
                        //Copy employees 
                        doc.to_employees = [];
                        var to_employees = frappe.model.add_child(doc, "to_employees");
                        to_employees.employee = frm.doc.from_employee;
                        doc.refresh_field("to_employees");
                    }
                );
		    });
		    frm.add_custom_button("Redirect Message", function() {
                frappe.new_doc("Internal Message", {}, 
                    doc=>{
                        doc.subject = frm.doc.subject;
                        const reply = get_reply_message(frm);
                        doc.description = reply;
                        doc.inbox_reference_id = frm.doc.name;
                        doc.reference_id = frm.doc.internal_reference_id;
                        doc.message_status = "Forwarded";
                        doc.conversation_id = frm.doc.conversation_id;
                        
                        //Copy attachements
                        doc.attachments = [];
                        for (let i = 0; i < frm.doc.attachments.length; i++) {
                            let row = frappe.model.add_child(doc, "attachments");
                            // console.log(frm.doc.attachments[i]);
                            row.attachment = frm.doc.attachments[i].attachment;
                        }
                        
                        //Copy employees
                        doc.to_employees = [];
                        doc.refresh_field("to_employees");
                    }
                );
		    });
		}
		
	}
})

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



function add_quick_outbox_buttons(frm)
{
    const targetDiv = document.getElementsByClassName("form-sidebar overlay-sidebar hidden-xs hidden-sm")[0].parentElement;
    if (targetDiv) {
        const btn = document.createElement("button");
        btn.textContent = "+ صادر جديد";
        btn.className = "btn btn-primary mt-3 w-100"; // Frappe/Bootstrap style
        btn.onclick = () => {
            // frappe.new_doc("Internal Message", {});
            const report_url = `/app/internal-message/new-internal-message`;
            window.open(report_url, '_blank'); // open in new tab
        };
        targetDiv.appendChild(btn);
    }
}
function add_quick_outbox_list_buttons(frm)
{
    const targetDiv = document.getElementsByClassName("form-sidebar overlay-sidebar hidden-xs hidden-sm")[0].parentElement;
    if (targetDiv) {
        const btn = document.createElement("button");
        btn.textContent = "عرض قائمة الصدار";
        btn.className = "btn btn-default ellipsis w-100"; // Frappe/Bootstrap style
        btn.onclick = () => {
            const report_url = `/app/internal-message`;
            window.open(report_url, '_blank'); // open in new tab
        };
        targetDiv.appendChild(btn);
    }
}
function hide_sidebar(frm){
    var element = document.getElementsByClassName("form-sidebar");
    element[0].hidden = true;
}

function get_reply_message(frm)
{
    let original_sender = frm.doc.owner; 
    let original_date = frappe.datetime.global_date_format(frm.doc.creation);
    let original_content = frm.doc.description || ";
    
    let reply_template = `
        <p><br></p>
        <p><br></p>
        
        <blockquote class="original-message" style="margin: 0; padding: 10px 15px; border-right: 4px solid #1b4332; color: #4b5563; font-style: italic;">
             <span style="font-size: 13px; color: #6b7280; font-weight: bold; display: block; margin-bottom: 5px;">
                الرد على الرسالة السابقة:
            </span>
            <span style="font-size: 11px; color: #9ca3af; display: block; margin-bottom: 10px;">
                من: ${original_sender} | بتاريخ: ${original_date}
            </span>
            
            ${original_content}
        </blockquote>
    `;

    return reply_template;
}