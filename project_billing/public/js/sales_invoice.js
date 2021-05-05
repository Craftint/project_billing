frappe.ui.form.on('Sales Invoice', {
    project: function (frm) {
        if (frm.doc.project) {
            frappe.call({
                "method": "project_billing.project_billing.utils.get_billing_details",
                "args": {
                    'doc': frm.doc
                },
                callback: function (r) {
                    if (r.message) {
                        let tasks = r.message[0];
                        let invoice_retention_amount = r.message[1];
                        if (tasks.length > 0) {
                            frm.clear_table('items');
                            tasks.forEach(function (task) {
                                let row = frm.add_child('items', {
                                    item_code: task.item_code,
                                    item_name: task.item_name,
                                    rate: task.rate,
                                    full_rate: task.full_rate,
                                    uom: task.uom,
                                    qty: task.qty,
                                    description: task.description,
                                    conversion_factor: task.conversion_factor,
                                    income_account: task.income_account,
                                    amount: task.amount,
                                    full_amount: task.full_amount,
                                    retention_amount: task.retention_amount,
                                    reference_task: task.reference_task,
                                    billable_amount: task.billable_amount,
                                    task_progress: task.task_progress,
                                    progress_billed: task.progress_billed,
                                    progress_qty: task.progress_qty,
                                    percent_billed: task.percent_billed,
                                    sales_order: task.sales_order,
                                    so_detail: task.so_detail
                                });
                                frm.trigger('validate');
                                frm.refresh_fields();
                                frm.set_value('invoice_retention_amount', invoice_retention_amount);
                            });
                        } else {
                            frappe.show_alert({
                                message: __('No Tasks for the selected Project indicate billable progress, please try after updating Task progress / status'),
                                indicator: 'orange'
                            });
                            // frm.set_value('project', '');
                        }
                    }
                }
            });
        } else {
            frm.clear_table('items');
        }
    }
});
