# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "project_billing"
app_title = "Project Billing"
app_publisher = "earthians"
app_description = "Extension to Project to allow Task Progressive Billing"
app_icon = "octicon octicon-rocket"
app_color = "purple"
app_email = "info@earthianslive.com"
app_license = "MIT"

fixtures = [{"dt":"Custom Field",
				"filters": [
					["name", "in", (
						"Task-task_item", "Task-task_item_uom",
						"Task-task_item_group", "Task-billable_amount",
						"Task-billing_details", "Task-percent_billed",
						"Task-progress_billed","Task-column_break_24",
						"Sales Invoice-billing_history", "Sales Invoice-project_billing_history",
						"Sales Invoice Item-progress_billed", "Sales Invoice Item-percent_billed",
						"Sales Invoice Item-billable_amount", "Sales Invoice Item-reference_task",
						"Sales Invoice Item-task_progress", "Sales Invoice Item-full_amount",
						"Sales Invoice Item-full_rate", "Sales Invoice Item-progress_qty",
						"Sales Invoice Item-billable_amount",
						"Project-retention_percentage", "Project-total_retention_amount",
						"Project-advance_percentage",
						"Project Template Task-task_item", "Project Template Task-task_item_uom",
						"Project Template Task-task_item_group",
						"Project Template Task-project_billing_fields_column_break",
						"Project Template Task-project_template_description_section",
						"Project Template Task-billable_amount", "Project Template Task-is_milestone",
						"Sales Order-project_template", "Sales Order-sales_order_project_template_column_break"
						)
					]
				]
			},
			{"dt":"Property Setter",
				"filters": [["doc_type", "in", ("Project", "Task", "Project Template Task")]]
			},
			{"dt":"Print Format",
				"filters": [["name", "=", ("Project Progressive Invoice")]]
			}
		]

doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
	"Project": "public/js/project.js",
	"Task": "public/js/task.js",
	"Sales Order": "public/js/sales_order.js"
}

doc_events = {
	"Task": {
		"before_insert": "project_billing.project_billing.utils.create_item_from_task",
		"validate": "project_billing.project_billing.utils.validate_task_billing_details"
	},
	"Sales Invoice": {
		"validate": "project_billing.project_billing.utils.validate_items_and_set_history",
		"on_submit": "project_billing.project_billing.utils.update_project_and_task",
		"on_cancel": "project_billing.project_billing.utils.update_project_and_task"
	},
	"Project Template": {
		"validate": "project_billing.project_billing.utils.create_items_from_project_template",
	},


}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/project_billing/css/project_billing.css"
# app_include_js = "/assets/project_billing/js/project_billing.js"

# include js, css files in header of web template
# web_include_css = "/assets/project_billing/css/project_billing.css"
# web_include_js = "/assets/project_billing/js/project_billing.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "project_billing.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "project_billing.install.before_install"
# after_install = "project_billing.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "project_billing.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"project_billing.tasks.all"
# 	],
# 	"daily": [
# 		"project_billing.tasks.daily"
# 	],
# 	"hourly": [
# 		"project_billing.tasks.hourly"
# 	],
# 	"weekly": [
# 		"project_billing.tasks.weekly"
# 	]
# 	"monthly": [
# 		"project_billing.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "project_billing.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "project_billing.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "project_billing.task.get_dashboard_data"
# }
