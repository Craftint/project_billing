import frappe
import json
from frappe import _, bold
from frappe.utils import flt, today, add_days
from erpnext.stock.get_item_details import get_item_details
from erpnext import get_default_currency

# Task Hooks
def create_item_from_task(doc, method):
	'''
	before insert Task
	Create Item for billing for is_milestone
	'''
	if doc.project:
		so_detail = ''
		project_template, sales_order = frappe.db.get_value('Project', doc.project, ['project_template', 'sales_order'])
		if sales_order:
			sales_order_doc = frappe.get_doc("Sales Order", sales_order)
			so_detail = [so_item for so_item in sales_order_doc.items if so_item.get('item_code') == doc.subject]
			doc.so_detail = so_detail[0].get('name')

		if project_template:
			project_template_doc = frappe.get_doc("Project Template", project_template)

			if project_template_doc:
				template_task = [template for template in project_template_doc.tasks if template.get('subject') == doc.subject]
				if template_task and template_task[0]:
					if len(template_task) > 1:
						frappe.throw(_('Project Template contains multiple Tasks with same Subject {}')
							.format(bold(template_task[0].get('subject'))), title = _('Did not Create Tasks'))
					if template_task[0].get('is_milestone') == 1:
						doc.is_milestone = template_task[0].get('is_milestone')
						doc.task_item = template_task[0].get('task_item')
						doc.task_item_uom = template_task[0].get('task_item_uom')
						doc.task_item_group = template_task[0].get('task_item_group')
						doc.billable_amount = so_detail[0].get('amount') if so_detail else template_task[0].get('billable_amount')
	if not doc.is_milestone:
		return

	# Milestone task, create new Item or link existing
	doc.item = get_item_link(doc)


# Project Template Task
def create_items_from_project_template(doc, method):
	'''
	before insert Project Template
	Create Items for all milestone tasks
	'''
	if not doc.tasks:
		return

	for task in doc.tasks:
		if task.is_milestone:
			task.task_item = get_item_link(task)
			task.task_item_uom = task.task_item_uom if task.task_item_uom else 'Percent'
			task.task_item_group = task.task_item_group if task.task_item_group else 'All Item Groups'
			task.description = task.description if task.description else task.task_item


# Sales Invoice hooks
def validate_task_billing_details(doc, method):
	'''
	validate Task
	Validate billable amounts with Project Estimate
	'''
	if flt(doc.progress) < flt(doc.progress_billed):
		frappe.throw(_('Task Progress cannot be less than the percentage already Invoiced'))

	if doc.is_milestone and flt(doc.billable_amount) <= 0:
		frappe.throw(_('Billable Amount is mandatory for Milestone Tasks'))

	if doc.is_milestone and not doc.project:
		frappe.throw(_('Project is mandatory for Milestone Tasks'))

	tasks = frappe.db.get_all('Task',
		filters={
			'project': doc.project,
			'is_milestone': 1,
			'name': ['!=', doc.name]
		},
		fields=[
			'sum(billable_amount) as total_billable_amount'
		])

	max_total_billable = flt(frappe.db.get_value('Project', doc.project, 'total_sales_amount'))
	if max_total_billable <= 0:
		max_total_billable = flt(frappe.db.get_value('Project', doc.project, 'estimated_costing'))

	total_tasks_billable = flt(doc.billable_amount) + flt(tasks[0].total_billable_amount) if tasks and tasks[0] else 0
	if max_total_billable > 0 and total_tasks_billable > max_total_billable:
		frappe.throw(_('Total billable amount ({}) for all Milestone Tasks exceeds the Estimated Cost / Total Sales Amount of Project ({})')
			.format(
				frappe.utils.fmt_money(abs(total_tasks_billable), currency=get_default_currency()),
				frappe.utils.fmt_money(abs(max_total_billable), currency=get_default_currency())
			),
			title=_('Did not Save')
		)


def update_project_and_task(doc, method):
	'''
	on submit Sales Invoice
	on cancel Sales Invoice
	Update Task billed percentage
	Update Project invoiced retention amount
	'''
	if doc.project:
		# Update Task billed percentage
		for item in doc.items:
			if item.reference_task and frappe.db.exists('Task', item.reference_task):
				progress_billed, percent_billed = frappe.db.get_value('Task', item.reference_task, ['progress_billed', 'percent_billed'])
				if doc.docstatus == 1:
					progress_billed = progress_billed + item.progress_qty
					percent_billed = percent_billed + item.qty
				else:
					progress_billed = progress_billed - item.progress_qty
					percent_billed = percent_billed - item.qty
					# Also set progress_billed, so that the invoice can be amended
					frappe.db.set_value(item.doctype, item.name, 'progress_billed', progress_billed)
					frappe.db.set_value(item.doctype, item.name, 'percent_billed', percent_billed)

				frappe.db.set_value('Task', item.reference_task, 'progress_billed', progress_billed)
				frappe.db.set_value('Task', item.reference_task, 'percent_billed', percent_billed)

		# Update Project Retention Amount
		if doc.invoice_retention_amount and doc.invoice_retention_amount > 0:
			total_retention_amount = frappe.db.get_value('Project', doc.project, 'total_retention_amount')
			if doc.docstatus == 1:
				total_retention_amount = total_retention_amount + doc.invoice_retention_amount
			else:
				total_retention_amount = total_retention_amount - doc.invoice_retention_amount

			frappe.db.set_value('Project', doc.project, 'total_retention_amount', total_retention_amount)


# Sales Invoice hooks
def validate_items_and_set_history(doc, method):
	'''
	validate Sales Invoice
	'''
	doc.invoice_retention_amount = 0
	if doc.project:
		for item in doc.items:
			if item.reference_task:
				task_details = frappe.db.get_value('Task', item.reference_task, ['progress_billed', 'percent_billed', 'progress'], as_dict=1)
				retention_percentage, advance_percentage = frappe.db.get_value('Project', doc.project, ['retention_percentage', 'advance_percentage'])

				# Verify if the progress_billed has changed after creating this invoice
				if item.percent_billed != task_details.percent_billed:
					frappe.throw(_('Progress of Tasks for billing does not match, please reselect Project to fetch items based on current progress'))

				# Verify if billed qty is more than billable progress
				billable_qty, progress_qty = get_billable_qty(task_details, advance_percentage)

				if flt(item.qty) > billable_qty or item.progress_qty > progress_qty:
					frappe.throw(_('Quantity exceeds Task billable quantity {} percent, Please verify Row #{}')
						.format(frappe.bold(billable_qty), item.idx))

				# Ensure no retention for advance
				if item.progress_qty == 0:
					retention_percentage = 0

				# Billing rate shouldn't be changed, recalculate and set rate
				# Also set amount based on rate and invoice quantity
				actual_billable_amount = get_actual_billable_amount(item, retention_percentage, advance_percentage)
				item.full_rate = (flt(item.billable_amount) / 100) * flt(doc.plc_conversion_rate) / flt(doc.conversion_rate)
				item.rate = (flt(actual_billable_amount) / 100) * flt(doc.plc_conversion_rate) / flt(doc.conversion_rate)
				item.full_amount = item.qty * item.full_rate
				# item.amount =  item.qty * item.rate

				# NOTE: full amount is in invoice currency, and qty is editable - recalculate
				item.retention_amount = (flt(item.billable_amount) / 100) * flt(item.qty) - \
					(flt(actual_billable_amount) / 100) * flt(item.qty)

				doc.invoice_retention_amount += item.retention_amount

	# Set billing history
	set_billing_history(doc)


@frappe.whitelist()
def get_billing_details(doc):
	'''
	get billable task details for the project
	invoked from Sales Invoice, on project
	NOTE:
	1 - to deal with advance, play on billing qty
	2 - to deal with retention, play on rate (via the actual billable amount)
	'''
	invoice = json.loads(doc)
	if not invoice.get('project'):
		return

	project_details = frappe.db.get_value('Project', invoice.get('project'),
		['percent_complete_method', 'retention_percentage', 'advance_percentage', 'sales_order',
		'total_sales_amount', 'total_billed_amount', 'total_retention_amount'],
		as_dict=1
	)

	filters = {'project': invoice.get('project'), 'is_milestone': 1, 'progress_billed': ['<', 100]}
	if project_details.percent_complete_method == 'Task Completion':
		filters.update({'status': 'Completed'})
	elif project_details.percent_complete_method in ['Task Progress']: # TODO: ['Task Progress', 'Task Weight']
		filters.update({'progress': ['<=', 100]})
	else:
		frappe.msgprint(_('Project Complete Method is not supported, please select Items manually'), alert=True, indicator='orange')

	tasks = frappe.db.get_all('Task', filters=filters, fields=['name', 'task_item', 'task_item_group', 'description',
		'task_item_uom', 'billable_amount', 'status', 'progress', 'progress_billed', 'percent_billed', 'task_weight', 'so_detail'])

	if not tasks:
		frappe.throw(_('No Tasks related to this Project indicate billable progress, please try after updating Task progress / status'))

	items = []
	invoice_retention_amount = 0.0

	for task in tasks:
		if project_details.percent_complete_method != 'Task Completion':
			if task.progress_billed != 0 and task.progress <= task.progress_billed:
				continue

		item_details = get_item_details({
			'doctype': 'Sales Invoice',
			'item_code': task.task_item,
			'company': invoice.get('company'),
			'selling_price_list': invoice.get('price_list'),
			'price_list_currency': invoice.get('currency'),
			'plc_conversion_rate': invoice.get('plc_conversion_rate'),
			'conversion_rate': invoice.get('conversion_rate')
		})

		if project_details.percent_complete_method == 'Task Progress':
			item_details['qty'], item_details['progress_qty'] = get_billable_qty(task, project_details.advance_percentage)
			item_details['billable_amount'] = flt(task.billable_amount)

		# Check qty here again as get_billable_qty may return 0
		if item_details['qty'] <= 0:
			continue

		# no retention_percentage if advance
		if item_details['progress_qty'] == 0:
			retention_percentage = 0
		else:
			retention_percentage = project_details.retention_percentage

		# get actual billable amount
		actual_billable_amount = get_actual_billable_amount(item_details, retention_percentage, project_details.advance_percentage)

		item_details['full_rate'] = (flt(task.billable_amount) / 100) * \
			flt(invoice.get('plc_conversion_rate')) / flt(invoice.get('conversion_rate'))
		item_details['rate'] = (flt(actual_billable_amount) / 100) * \
			flt(invoice.get('plc_conversion_rate')) / flt(invoice.get('conversion_rate'))
		item_details['full_amount'] = item_details['qty'] * item_details['full_rate']
		# item_details['amount'] =  item_details['qty'] * item_details['rate']
		item_details['uom'] = task.task_item_uom
		item_details['reference_task'] = task.name
		item_details['task_progress'] = task.progress
		item_details['progress_billed'] = task.progress_billed
		item_details['percent_billed'] = task.percent_billed
		item_details['sales_order'] = project_details.sales_order
		item_details['so_detail'] = task.so_detail

		# NOTE: full amount is in invoice currency hence recalulating. basically, full_amount - actual_billable_amount
		item_details['retention_amount'] = (flt(item_details['billable_amount']) / 100) * flt(item_details['qty']) - \
			(flt(actual_billable_amount) / 100) * flt(item_details['qty'])

		# add item for billing
		items.append(item_details)
		invoice_retention_amount += item_details['retention_amount']

	return items, invoice_retention_amount


# Helpers
def get_actual_billable_amount(task, retention=0, advance=0):
	'''
	Return actual_billable_amount: billable amount for the task after retention amount.
	'''
	if not task:
		return 0

	# pump up the retention percentage to accommodate retention not retained for advance
	retention_percentage = flt(retention * flt(100 / (100 - advance)))

	# actual billable amount based on retention percentage
	actual_billable_amount = flt(task.billable_amount) - \
		(flt(task.billable_amount) * (retention_percentage / 100) if retention_percentage > 0 else 0)

	return actual_billable_amount


def get_billable_qty(task, advance=0):
	'''
	Return:
	qty: billable qty to maintain constancy of the task billable amount (advance is booked regardless of progress)
	progress_qty: actual progress that is not yet billed
	'''
	if not task:
		return 0, 0

	# let's not allow progress to be billed if advance is not fully booked
	if advance > 0 and task.percent_billed < advance:
		return abs(advance - task.percent_billed), 0

	progress_qty = flt(task.progress - task.progress_billed)
	qty = abs(progress_qty - (flt(advance) * progress_qty / 100))

	return qty, progress_qty


def set_billing_history(doc):
	'''
	set billing history html only if the Sales Invoice is a 'project progressive invoice'
	'''
	if doc.project and any(bool(item.get('reference_task')) for item in doc.items):
		past_invoices = frappe.db.get_all('Sales Invoice',
			filters = {
				'project': doc.project,
				'name': ['!=', doc.name],
				'docstatus': 1
				},
			fields=['name', 'posting_date', 'status', 'outstanding_amount']
		)

		item_details = frappe.db.get_all('Sales Invoice Item',
			filters = {
				'parent': ['in', [invoice_name.get('name') for invoice_name in past_invoices]],
				'reference_task': ['!=', '']
				},
			fields = ['parent', 'item_code', 'reference_task', 'qty', 'amount', 'billable_amount']
		)

		for item_detail in item_details:
			invoice_status = [inv for inv in past_invoices if inv['name'] == item_detail['parent']]
			item_detail.update(invoice_status[0])

		doc.project_billing_history = frappe.render_template('templates/includes/billing_history.html',
			dict(items=item_details, currency=doc.currency))
	else:
		doc.project_billing_history = ''


def get_item_link(doc):
	'''
	return item link name if exists
	else return new item link name
	'''
	if doc.task_item and frappe.db.exists('Item', doc.task_item):
		return doc.task_item
	elif doc.subject and frappe.db.exists('Item', doc.subject):
		return doc.subject
	else:
		if not doc.task_item and not doc.subject:
			frappe.throw(_('Mandatory fields required in Task <br><br><li> Subject / Item</li>'))

		item = frappe.get_doc({
			'doctype': 'Item',
			'item_code': doc.task_item or doc.subject,
			'item_name': doc.task_item or doc.subject,
			'item_group': doc.task_item_group or 'All Item Groups',
			'description': doc.description or doc.task_item or doc.subject,
			'stock_uom': doc.task_item_uom or 'Percent',
			'is_stock_item': 0,
			'is_sales_item': 1,
			'is_service_item': 1,
			'is_purchase_item': 0,
			'show_in_website': 0,
			'is_pro_applicable': 0,
			'disabled': 0
		}).insert(ignore_permissions=True)
		return item.name
