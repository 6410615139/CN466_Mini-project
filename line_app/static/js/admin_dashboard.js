// Filter by Admin Status
function filterByAdminStatus() {
    const filter = document.getElementById('adminFilter').value.toLowerCase();
    const table = document.getElementById('usersTable');
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) { // Skip header row
        const cell = rows[i].getElementsByTagName('td')[2]; // Admin status column
        if (filter === 'all' || (cell && cell.textContent.toLowerCase() === filter)) {
            rows[i].style.display = '';
        } else {
            rows[i].style.display = 'none';
        }
    }
}

function deleteUser(userId) {
    if (confirm("Are you sure you want to delete this user?")) {
        fetch(`/admin/delete_user/${userId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
        })
            .then(response => {
                if (response.ok) {
                    alert("User deleted successfully!");
                    document.getElementById(`user-row-${userId}`).remove();
                } else {
                    alert("Failed to delete user.");
                }
            })
            .catch(error => console.error("Error:", error));
    }
}