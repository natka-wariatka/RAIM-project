// Global JavaScript functions and configurations

// Format date with Moment.js
function formatDate(dateString) {
    return moment(dateString).format('MMMM D, YYYY');
}

// Format time with Moment.js
function formatTime(timeString) {
    return moment(timeString, 'HH:mm').format('h:mm A');
}

// Add validation for the patient registration form
document.addEventListener('DOMContentLoaded', function() {
    const patientForm = document.getElementById('patient-form');
    
    if (patientForm) {
        patientForm.addEventListener('submit', function(event) {
            // Simple form validation
            const firstName = document.getElementById('first_name').value.trim();
            const lastName = document.getElementById('last_name').value.trim();
            const dateOfBirth = document.getElementById('date_of_birth').value;
            const email = document.getElementById('email').value.trim();
            const specialty = document.getElementById('specialty').value;
            
            let isValid = true;
            let errorMessage = '';
            
            if (!firstName) {
                errorMessage += 'First name is required.\n';
                isValid = false;
            }
            
            if (!lastName) {
                errorMessage += 'Last name is required.\n';
                isValid = false;
            }
            
            if (!dateOfBirth) {
                errorMessage += 'Date of birth is required.\n';
                isValid = false;
            } else {
                // Check if date of birth is in the past
                const dobDate = new Date(dateOfBirth);
                const today = new Date();
                
                if (dobDate >= today) {
                    errorMessage += 'Date of birth must be in the past.\n';
                    isValid = false;
                }
            }
            
            if (!email) {
                errorMessage += 'Email is required.\n';
                isValid = false;
            } else if (!isValidEmail(email)) {
                errorMessage += 'Please enter a valid email address.\n';
                isValid = false;
            }
            
            if (!specialty) {
                errorMessage += 'Please select a specialist.\n';
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
                alert('Please correct the following errors:\n\n' + errorMessage);
            }
        });
    }
});

// Email validation function
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
