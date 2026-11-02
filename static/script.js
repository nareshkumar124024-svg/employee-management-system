const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", function (event) {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        if (!email || !password) {
            event.preventDefault();
            alert("Please enter your email and password.");
        }
    });
}


const employeeSearch = document.getElementById("employeeSearch");

if (employeeSearch) {
    employeeSearch.addEventListener("input", function () {
        const query = this.value.toLowerCase().trim();

        document.querySelectorAll("#employeeTable tbody tr").forEach(row => {
            const searchableText = row.textContent.toLowerCase();
            row.hidden = !searchableText.includes(query);
        });
    });
}

const editDialog = document.getElementById("editDialog");
const editForm = document.getElementById("editForm");

document.querySelectorAll("[data-edit]").forEach(button => {
    button.addEventListener("click", function () {
        const id = this.dataset.id;

        editForm.action = "/employees/edit/" + encodeURIComponent(id);
        document.getElementById("editName").value = this.dataset.name;
        document.getElementById("editEmail").value = this.dataset.email;
        document.getElementById("editPhone").value = this.dataset.phone;
        document.getElementById("editDepartment").value =
            this.dataset.department;
        document.getElementById("editSalary").value = this.dataset.salary;

        editDialog.showModal();
    });
});

const closeDialog = document.getElementById("closeDialog");

if (closeDialog && editDialog) {
    closeDialog.addEventListener("click", () => editDialog.close());
}

document.querySelectorAll(".delete-form").forEach(form => {
    form.addEventListener("submit", function (event) {
        if (!confirm("Are you sure you want to delete this employee?")) {
            event.preventDefault();
        }
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const dropdown = document.getElementById("employeeDropdown");
    if (!dropdown) return;

    const search = document.getElementById("employeeSearch");
    const selectedId = document.getElementById("employee_id");
    const optionsBox = document.getElementById("employeeOptions");
    const options = Array.from(
        optionsBox.querySelectorAll(".employee-option")
    );

    const noResults = document.createElement("div");
    noResults.className = "no-results";
    noResults.textContent = "No employees found";

    function filterEmployees() {
        const query = search.value.trim().toLowerCase();
        let matches = 0;

        options.forEach(function (option) {
            const isMatch = option.dataset.search.includes(query);
            option.hidden = !isMatch;
            if (isMatch) matches++;
        });

        noResults.remove();
        if (matches === 0) optionsBox.appendChild(noResults);

        optionsBox.style.display = "block";
    }

    search.addEventListener("focus", filterEmployees);
    search.addEventListener("input", function () {
        selectedId.value = "";
        filterEmployees();
    });

    options.forEach(function (option) {
        option.addEventListener("click", function () {
            search.value = option.textContent.trim();
            selectedId.value = option.dataset.id;
            optionsBox.style.display = "none";
            noResults.remove();
        });
    });

    document.addEventListener("click", function (event) {
        if (!dropdown.contains(event.target)) {
            optionsBox.style.display = "none";
        }
    });

    const form = dropdown.closest("form");
    if (form) {
        form.addEventListener("submit", function (event) {
            if (!selectedId.value) {
                event.preventDefault();
                search.setCustomValidity(
                    "Please select an employee from the dropdown."
                );
                search.reportValidity();
            } else {
                search.setCustomValidity("");
            }
        });
    }

    search.addEventListener("input", function () {
        search.setCustomValidity("");
    });
});
