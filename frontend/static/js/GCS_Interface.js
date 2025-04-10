/**
 * GCS Interface
 *
 * Responsible for switching tabs/pages, button logic, etc.
 * Updates stats on the webpage based on the API and handles the password screen.
 */

/// DYNAMIC MODULE SWITCHING CODE
function updateModules(selected) {
	document.querySelectorAll(".module").forEach((elem) => {
		if (elem.classList.contains(selected)) {
			elem.classList.remove("hidden");
		} else {
			elem.classList.add("hidden");
		}
	});
}

window.addEventListener("load", function () {
	// Get selected page
	var selected = window.location.hash
		? this.window.location.hash.substring(1)
		: document.querySelector("nav a").href.split("#")[1];
	console.log(selected);

	// Determine which modules are "selected"
	updateModules(selected);

	// Highlight selected tab link
	//document.querySelector(`a[href='#${selectedTab}']`).classList.add(...selectedClasses);

	// Switch tabs when links are pressed
	document.querySelectorAll("nav a").forEach((elem) => {
		elem.addEventListener("click", (event) => {
			event.preventDefault();

			// Switch tabs
			selected = elem.href.split("#")[1];
			updateModules(selected);

			// Highlight new selected tab link
			/*
			document.querySelectorAll("nav a").forEach((elem) => {
				elem.classList.remove(...selectedClasses);
			});
			document.querySelector(`a[href='#${tab}']`).classList.add(...selectedClasses);
			*/

			// Update URL
			history.replaceState(null, "", `#${selected}`);

			// Dispatch page resize event (since elements are moving around)
			window.dispatchEvent(new Event("resize"));
		});
	});
});
