frappe.ui.form.on('Project', {
	setup: function (frm) {
		frm.set_query('advance_invoice', {
			'docstatus': 1,
			'customer': frm.doc.customer,
			'project': frm.doc.name
		});
	},

	refresh: function (frm) {
		if (frm.doc.total_billed_amount > 0) {
			frm.set_df_property('retention_percentage', 'read_only', 1);
			frm.set_df_property('percent_complete_method', 'read_only', 1);
			frm.set_df_property('advance_percentage', 'read_only', 1);
		}
	},

	advance_percentage: function(frm) {
		if (frm.doc.advance_invoice > 0 && !frm.doc.total_sales_amount > 0) {
			frappe.throw(__('You cannot set advance amount without a valid Total Sales Amount.'))
		}
	},

	advance_invoice: function (frm) {
		if (frm.doc.advance_invoice) {
			frappe.db.get_value('Sales Invoice', frm.doc.advance_invoice, ['base_grand_total', 'base_rounded_total'])
				.then(r => {
					let advance_invoice_amount = 0
					if (r.message.base_rounded_total > 0) {
						advance_invoice_amount = r.message.base_rounded_total;
					} else {
						advance_invoice_amount = r.message.base_grand_total;
					}
					if (frm.doc.advance_percentage > 0 && frm.doc.total_sales_amount > 0) {
						let required_advance = frm.doc.total_sales_amount * (frm.doc.advance_percentage / 100)
						if (advance_invoice_amount < required_advance) {
							frm.set_value({
								'advance_invoice': '',
								'advance_invoice_amount': 0
							});
							frappe.throw(__('Advance Invoice amount should at least be {0}', [required_advance]))
						}
					}
					frm.set_value('advance_invoice_amount', advance_invoice_amount);
				})
		} else {
			frm.set_value('advance_invoice_amount', 0);
		}
		frm.refresh_field('advance_invoice_amount');
	}
});
