// Open modal
document.getElementById("open-modal").onclick = function () {
    document.getElementById("addPlateModal").style.display = "block";
};

// Close modal
document.getElementById("close-modal").onclick = function () {
    document.getElementById("addPlateModal").style.display = "none";
};

// Close modal when clicking outside of it
window.onclick = function (event) {
    if (event.target === document.getElementById("addPlateModal")) {
        document.getElementById("addPlateModal").style.display = "none";
    }
};