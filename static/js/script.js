// ================================
// CHATBOT I DIAGNOZA – SOCKET.IO
// ================================
document.addEventListener("DOMContentLoaded", () => {
    const socket = io(); // Połączenie z serwerem

    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const diagnoseBtn = document.getElementById("diagnoseBtn");
    const chatbox = document.getElementById("chatbox");

    // Dodaj wiadomość do czatu
    function addMessage(role, text) {
        const message = document.createElement("div");
        message.classList.add("mb-3", role === 'user' ? 'text-end' : 'text-start');
        message.innerHTML = `
            <div class="d-inline-block p-2 rounded-3 ${role === 'user' ? 'bg-success text-light' : 'bg-light text-dark'}">
                <strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> ${text}
            </div>
        `;
        chatbox.appendChild(message);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    // Wysłanie wiadomości
    if (sendBtn) {
        sendBtn.addEventListener("click", () => {
            const text = userInput.value.trim();
            if (!text) return;

            addMessage("user", text);
            socket.emit("user_message", { text });
            userInput.value = "";
        });
    }

    // Wysłanie żądania diagnozy
    if (diagnoseBtn) {
        diagnoseBtn.addEventListener("click", () => {
            socket.emit("diagnose_request");
        });
    }

    // Odbiór odpowiedzi od bota
    socket.on("bot_response", (data) => {
        addMessage("assistant", data.response);
    });

    // Obsługa Enter
    if (userInput) {
        userInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendBtn.click();
        });
    }
});

// ================================
// FORMATOWANIE DATY I CZASU
// ================================

function formatDate(dateString) {
    return moment(dateString).format('MMMM D, YYYY');
}

function formatTime(timeString) {
    return moment(timeString, 'HH:mm').format('h:mm A');
}

// ================================
// WALIDACJA FORMULARZA PACJENTA
// ================================
document.addEventListener('DOMContentLoaded', function () {
    const patientForm = document.getElementById('patient-form');

    if (patientForm) {
        patientForm.addEventListener('submit', function (event) {
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

// ================================
// WALIDACJA EMAILA
// ================================
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
