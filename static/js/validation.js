// Client-side validation for form fields

document.addEventListener('DOMContentLoaded', function() {
    // Name validation
    const nameInputs = document.querySelectorAll('input[name="first_name"], input[name="last_name"]');
    nameInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value;
            const letterOnlyRegex = /^[A-Za-z]+$/;
            
            if (value && !letterOnlyRegex.test(value)) {
                this.classList.add('is-invalid');
                let feedbackEl = this.nextElementSibling;
                if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
                    feedbackEl = document.createElement('div');
                    feedbackEl.classList.add('invalid-feedback');
                    this.parentNode.insertBefore(feedbackEl, this.nextSibling);
                }
                feedbackEl.textContent = 'Must contain only letters';
            } else {
                this.classList.remove('is-invalid');
                const feedbackEl = this.nextElementSibling;
                if (feedbackEl && feedbackEl.classList.contains('invalid-feedback')) {
                    feedbackEl.remove();
                }
            }
        });
    });

    // Date of birth validation
    const dobInput = document.querySelector('input[name="date_of_birth"]');
    if (dobInput) {
        dobInput.addEventListener('input', function() {
            const value = this.value;
            const dateRegex = /^(\d{2})\.(\d{2})\.(\d{4})$/;
            
            if (value && !dateRegex.test(value)) {
                this.classList.add('is-invalid');
                let feedbackEl = this.nextElementSibling;
                if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
                    feedbackEl = document.createElement('div');
                    feedbackEl.classList.add('invalid-feedback');
                    this.parentNode.insertBefore(feedbackEl, this.nextSibling);
                }
                feedbackEl.textContent = 'Please enter a valid date in DD.MM.YYYY format';
            } else if (value) {
                const parts = value.split('.');
                const day = parseInt(parts[0], 10);
                const month = parseInt(parts[1], 10) - 1;
                const year = parseInt(parts[2], 10);
                
                const date = new Date(year, month, day);
                const today = new Date();
                
                if (
                    date.getDate() !== day || 
                    date.getMonth() !== month || 
                    date.getFullYear() !== year ||
                    date > today
                ) {
                    this.classList.add('is-invalid');
                    let feedbackEl = this.nextElementSibling;
                    if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
                        feedbackEl = document.createElement('div');
                        feedbackEl.classList.add('invalid-feedback');
                        this.parentNode.insertBefore(feedbackEl, this.nextSibling);
                    }
                    feedbackEl.textContent = 'Please enter a valid date that is not in the future';
                } else {
                    this.classList.remove('is-invalid');
                    const feedbackEl = this.nextElementSibling;
                    if (feedbackEl && feedbackEl.classList.contains('invalid-feedback')) {
                        feedbackEl.remove();
                    }
                }
            }
        });
    }

    // Blood test numerical values validation
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('test-result') || 
            e.target.classList.contains('ref-min') || 
            e.target.classList.contains('ref-max')) {
            
            const value = e.target.value;
            
            if (value && isNaN(parseFloat(value))) {
                e.target.classList.add('is-invalid');
                let feedbackEl = e.target.nextElementSibling;
                if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
                    feedbackEl = document.createElement('div');
                    feedbackEl.classList.add('invalid-feedback');
                    e.target.parentNode.insertBefore(feedbackEl, e.target.nextSibling);
                }
                feedbackEl.textContent = 'Please enter a valid number';
            } else {
                e.target.classList.remove('is-invalid');
                const feedbackEl = e.target.nextElementSibling;
                if (feedbackEl && feedbackEl.classList.contains('invalid-feedback')) {
                    feedbackEl.remove();
                }
            }
        }
    });
});
