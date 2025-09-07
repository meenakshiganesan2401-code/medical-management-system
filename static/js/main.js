// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Medicine search functionality
    const medicineSearchInput = document.getElementById('medicineSearch');
    const medicineSearchResults = document.getElementById('medicineSearchResults');
    
    if (medicineSearchInput && medicineSearchResults) {
        let searchTimeout;
        
        medicineSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                medicineSearchResults.style.display = 'none';
                return;
            }
            
            searchTimeout = setTimeout(() => {
                searchMedicines(query);
            }, 300);
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!medicineSearchInput.contains(e.target) && !medicineSearchResults.contains(e.target)) {
                medicineSearchResults.style.display = 'none';
            }
        });
    }

    // Dispense button functionality
    const dispenseButtons = document.querySelectorAll('.dispense-btn');
    dispenseButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const form = this.closest('form');
            const patientId = form.querySelector('input[name="patient_id"]').value;
            const prescriptionIndex = form.querySelector('input[name="prescription_index"]').value;
            
            // Show loading state
            this.classList.add('loading');
            this.disabled = true;
            
            // Submit form
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            })
            .then(response => {
                if (response.ok) {
                    // Show success message
                    showNotification('Medicine dispensed successfully!', 'success');
                    
                    // Update prescription status
                    const prescriptionCard = this.closest('.prescription-card');
                    prescriptionCard.classList.remove('active');
                    prescriptionCard.classList.add('dispensed');
                    
                    const statusBadge = prescriptionCard.querySelector('.prescription-status');
                    statusBadge.textContent = 'Dispensed';
                    statusBadge.classList.remove('active');
                    statusBadge.classList.add('dispensed');
                    
                    // Disable button
                    this.disabled = true;
                    this.textContent = 'Dispensed';
                } else {
                    throw new Error('Failed to dispense medicine');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to dispense medicine. Please try again.', 'error');
            })
            .finally(() => {
                this.classList.remove('loading');
                this.disabled = false;
            });
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Patient search functionality
    const patientSearchInput = document.getElementById('patientSearch');
    if (patientSearchInput) {
        patientSearchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const patientCards = document.querySelectorAll('.patient-card');
            
            patientCards.forEach(card => {
                const patientName = card.querySelector('.patient-name').textContent.toLowerCase();
                const patientAge = card.querySelector('.patient-age').textContent;
                
                if (patientName.includes(query) || patientAge.includes(query)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});

// Medicine search function
function searchMedicines(query) {
    // This would typically make an AJAX request to your backend
    // For now, we'll simulate with existing medicines on the page
    const medicineItems = document.querySelectorAll('.medicine-item');
    const results = [];
    
    medicineItems.forEach(item => {
        const name = item.dataset.name.toLowerCase();
        if (name.includes(query.toLowerCase())) {
            results.push({
                id: item.dataset.id,
                name: item.dataset.name,
                dosage: item.dataset.dosage,
                frequency: item.dataset.frequency
            });
        }
    });
    
    displaySearchResults(results);
}

// Display search results
function displaySearchResults(results) {
    const medicineSearchResults = document.getElementById('medicineSearchResults');
    
    if (results.length === 0) {
        medicineSearchResults.innerHTML = '<div class="medicine-search-item text-muted">No medicines found</div>';
    } else {
        medicineSearchResults.innerHTML = results.map(medicine => `
            <div class="medicine-search-item" onclick="selectMedicine('${medicine.id}', '${medicine.name}')">
                <div class="fw-bold">${medicine.name}</div>
                <small class="text-muted">${medicine.dosage} - ${medicine.frequency}</small>
            </div>
        `).join('');
    }
    
    medicineSearchResults.style.display = 'block';
}

// Select medicine from search results
function selectMedicine(medicineId, medicineName) {
    const medicineIdInput = document.getElementById('medicine_id');
    const medicineNameDisplay = document.getElementById('selectedMedicineName');
    const medicineSearchInput = document.getElementById('medicineSearch');
    const medicineSearchResults = document.getElementById('medicineSearchResults');
    
    if (medicineIdInput) {
        medicineIdInput.value = medicineId;
    }
    
    if (medicineNameDisplay) {
        medicineNameDisplay.textContent = medicineName;
        medicineNameDisplay.style.display = 'block';
    }
    
    if (medicineSearchInput) {
        medicineSearchInput.value = medicineName;
    }
    
    medicineSearchResults.style.display = 'none';
}

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Confirm action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy to clipboard', 'error');
    });
}
