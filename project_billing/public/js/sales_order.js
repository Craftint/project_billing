frappe.ui.form.on('Sales Order', {
    project_template: function (frm) {
        if (frm.doc.project_template) {
            frappe.db.get_doc('Project Template', frm.doc.project_template)
                .then(doc => {
                    frm.clear_table('items');
                    doc.tasks.forEach(task => {
                        let row = frm.add_child('items', {
                            item_code: task.task_item,
                            item_name: task.task_item,
                            description: (task.description ? task.description : task.task_item),
                            qty: 100,
                            uom: task.task_item_uom,
                            stock_uom: task.task_item_uom,
                            conversion_factor: 1,
                            rate: (task.billable_amount / 100) * (frm.doc.conversion_rate / frm.doc.plc_conversion_rate),
                            amount: 100 * ((task.billable_amount / 100) * (frm.doc.conversion_rate / frm.doc.plc_conversion_rate)),
                            plc_conversion_rate: frm.doc.plc_conversion_rate,
                            delivery_date: frm.doc.delivery_date
                        });
                    });
                    frm.refresh_field('items');
                });
        } else {
            frm.refresh_field('items');
        }
    }
});