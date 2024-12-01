let editingUserId = null;

function openEditModal(userId) {
    editingUserId = userId;

    // Fetch current user data
    const row = document.getElementById(`user-row-${userId}`);
    const username = row.cells[0].innerText;
    const parkingStatus = row.cells[3].innerText;
    const licensePlate = row.cells[4].innerText;
    const isAdmin = row.cells[2].innerText === "Yes";

    // Populate modal fields
    document.getElementById("editUsername").value = username;
    document.getElementById("editParkingStatus").value = parkingStatus.toLowerCase();
    document.getElementById("editLicensePlate").value = licensePlate;
    document.getElementById("editIsAdmin").checked = isAdmin;

    // Show modal
    document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
    editingUserId = null;
    document.getElementById("editModal").style.display = "none";
}

function submitEdit() {
    if (!editingUserId) return;

    // Collect updated data
    const data = {
        user_id: editingUserId,
        username: document.getElementById("editUsername").value,
        password: document.getElementById("editPassword").value || undefined,
        is_admin: document.getElementById("editIsAdmin").checked,
        parking_status: document.getElementById("editParkingStatus").value,
        license_plate: document.getElementById("editLicensePlate").value
    };

    // Send POST request to update user
    fetch("/admin/edit_user", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("User updated successfully!");
            location.reload();
        } else {
            alert("Failed to update user.");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        alert("There was an error with the submission.");
    });

    closeEditModal();
}