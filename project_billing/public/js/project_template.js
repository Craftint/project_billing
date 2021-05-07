frappe.ui.form.on('Project Template', {
    validate: function(frm) {
        if (frm.doc.tasks) {
            var valueArr = frm.doc.tasks.map(function(item){ return item.subject });
            var isDuplicate = valueArr.some(function(item, idx){ 
                return valueArr.indexOf(item) != idx 
            });
            if (isDuplicate == true) {
                frappe.throw(__('Tasks table contains multiple Tasks with same Subject'))
            }

        }
    }
});