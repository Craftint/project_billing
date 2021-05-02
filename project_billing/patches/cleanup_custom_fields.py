from frappe import delete_doc_if_exists

def execute():
    delete_doc_if_exists('Custom Field', 'Sales Invoice-past_billing_details')
    delete_doc_if_exists('Custom Field', 'Sales Invoice-project_retention_amount')
    delete_doc_if_exists('Custom Field', "Project-progressive_billing")
    delete_doc_if_exists('Custom Field', "Task-task_group")
    delete_doc_if_exists('Custom Field', "Task-uom")
    delete_doc_if_exists('Custom Field', "Task-item")
