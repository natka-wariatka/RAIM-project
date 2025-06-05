document.addEventListener("DOMContentLoaded", () => {
    const socket = io(); // Connect to the server
    const textarea = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const diagnoseBtn = document.getElementById("diagnoseBtn");
    const chatbox = document.getElementById("chatbox");

    function addMessage(role, text) {
        const message = document.createElement("div");
        message.classList.add("mb-3");
        message.classList.add(role === 'user' ? 'text-end' : 'text-start');
        message.innerHTML = `
            <div class="d-inline-block p-2 rounded-3 ${role === 'user' ? 'bg-success text-light' : 'bg-light text-dark'}">
                <strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> ${text}
            </div>
        `;
        chatbox.appendChild(message);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    sendBtn.addEventListener("click", () => {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage("user", text);
        socket.emit("user_message", { text });
        userInput.value = "";
    });

    diagnoseBtn.addEventListener("click", () => {
        socket.emit("diagnose_request");
    });

    textarea.addEventListener("input", () => {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    });

    textarea.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            document.getElementById("sendBtn").click();
        }
    });

    socket.on("bot_response", function(data) {
    if (data.type === 'text') {
        addMessage("assistant", data.response);
    };
    if (data.type === 'not_diagnosis') {
        addMessage("assistant", data.response);
    } else if (data.type === 'diagnosis') {
        addMessage("assistant", "Based on your answers, here are some possible conditions:");
        displayDiagnosisPopup(data.conditions, data.raw_text);
    }
    });

 function displayDiagnosisPopup(conditions, rawText) {
    const cardsContainer = document.getElementById("specialistCards");
    cardsContainer.innerHTML = "";

    const selectedSpecialistInput = document.getElementById("selectedSpecialist");
    selectedSpecialistInput.value = "";

    conditions.slice(0, 3).forEach((cond, index) => {
        const card = document.createElement("div");
        card.className = "col-md-4";

        card.innerHTML = `
            <div class="card border-primary shadow-sm h-100 specialist-card" data-specialist="${cond.specialist}">
                <div class="card-body">
                    <h5 class="card-title"><strong>Suggested Specialist:</strong> ${cond.specialist}</h5>
                    <p class="card-text"><strong>Condition:</strong> ${cond.condition_name}</p>
                    <p class="card-text"><strong>Probability:</strong> ${cond.probability}</p>
                </div>
            </div>
        `;

        card.querySelector('.specialist-card').addEventListener('click', function () {
            document.querySelectorAll('.specialist-card').forEach(el => {
                el.classList.remove('border-success');
            });
            this.classList.add('border-success');
            selectedSpecialistInput.value = this.dataset.specialist;
        });

        cardsContainer.appendChild(card);
    });

    const modal = new bootstrap.Modal(document.getElementById("diagnosisModal"));
    modal.show();
    document.getElementById("appointment_id").value = Date.now();
}

});
