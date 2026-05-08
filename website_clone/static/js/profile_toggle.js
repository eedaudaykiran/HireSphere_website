window.onload = function () {

    const roleField =
        document.getElementById("id_role");

    const workStatusField =
        document.getElementById("id_work_status");

    const companyField =
        document.getElementById("id_company_name");

    const workStatusRow =
        workStatusField.closest(".form-row") ||
        workStatusField.closest(".flex-container");

    const companyRow =
        companyField.closest(".form-row") ||
        companyField.closest(".flex-container");

    function toggleFields() {

        const role = roleField.value;

        console.log("Selected Role:", role);

        if (role === "candidate") {

            workStatusRow.style.display = "";

            companyRow.style.display = "none";
        }

        else if (role === "employer") {

            workStatusRow.style.display = "none";

            companyRow.style.display = "";
        }
    }

    toggleFields();

    roleField.addEventListener(
        "change",
        toggleFields
    );

};