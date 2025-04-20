/**
 * GCS Interface
 *
 * Responsible for switching tabs/pages, button logic, etc.
 * Updates stats on the webpage based on the API and handles the password screen.
 *
 * Functions and constants should be prefixed with "interface_" 
*/

/// DYNAMIC MODULE SWITCHING CODE
function interface_updateModules(selected) {
    document.querySelectorAll(".module").forEach((elem) => {
        if (elem.classList.contains(selected)) {
            elem.classList.remove("hidden");
        } else {
            elem.classList.add("hidden");
        }
    });
}

window.addEventListener("load", function () {
    const selectedClasses = ["selected"];

    // Get selected page
    var selected = window.location.hash
        ? this.window.location.hash.substring(1)
        : document.querySelector("nav a").href.split("#")[1];

    // Determine which modules are "selected"
    interface_updateModules(selected);

    // Highlight selected tab link
    document.querySelector(`a[href='#${selected}']`).classList.add(...selectedClasses);

    // Switch tabs when links are pressed
    document.querySelectorAll("nav a").forEach((elem) => {
        elem.addEventListener("click", (event) => {
            event.preventDefault();

            // Switch tabs
            selected = elem.href.split("#")[1];
            interface_updateModules(selected);

            // Highlight new selected tab link
			document.querySelectorAll("nav a").forEach((elem) => {
				elem.classList.remove(...selectedClasses);
			});
			document.querySelector(`a[href='#${selected}']`).classList.add(...selectedClasses);

            // Update URL
            history.replaceState(null, "", `#${selected}`);

            // Dispatch page resize event (since elements are moving around)
            window.dispatchEvent(new Event("resize"));
        });
    });
});

// FUNCTIONS FOR UPDATING VALUES IN THE INTERFACE
function interface_updateValue(item, value) {
    // Updates the value for a display item
    let elements = document.querySelectorAll(`.${item}`);

    // Use classes instead of IDs since IDs must be unique
    // and some items occur on multiple pages
    if (elements && elements.length > 0) {
        elements.forEach((elem) => {
            // Update value
            elem.value = value;
        });
    }
}
