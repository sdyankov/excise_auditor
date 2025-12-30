frappe.ui.form.on('Truth Source Settings', {
  refresh(frm) {
    frm.add_custom_button(__('Sync Permissions Now'), () => {
      frappe.call({
        method: 'excise_auditor.doctype.truth_source_settings.truth_source_settings.sync_permissions_now',
        callback() { frappe.msgprint(__('Permissions synced')); }
      });
    });
  }
});
