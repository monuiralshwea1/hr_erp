// hr_erp: common client enhancements (RTL polish + global helpers)
frappe.ready(() => {
	// ensure body gets RTL class on Arabic sites so tables align properly
	if (frappe.boot && frappe.boot.lang === "ar") {
		document.body.classList.add("rtl");
	}
});
