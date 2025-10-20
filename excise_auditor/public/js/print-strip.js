const hide_alt_print_actions = () => {
  document.querySelectorAll('.page-actions .custom-actions, .page-head .page-actions .custom-actions')
    .forEach(el => el.style.display = 'none');
};

const on_route_change = () => {
  const route = (frappe.get_route && frappe.get_route().join('/')) || location.pathname || '';
  if (route.toLowerCase().includes('print')) {
    setTimeout(hide_alt_print_actions, 50);
    setTimeout(hide_alt_print_actions, 300); // за късно рендерирани бутони
  }
};

if (window.frappe && frappe.router) {
  frappe.router.on('change', on_route_change);
}
document.addEventListener('DOMContentLoaded', on_route_change);
