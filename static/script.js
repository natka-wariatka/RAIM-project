document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const diagnoseBtn = document.getElementById("diagnoseBtn");
    const chatbox = document.getElementById("chatbox");

    function addMessage(role, text) {
        const message = document.createElement("div");
        message.classList.add(role);
        message.innerHTML = `<strong>${role === 'user' ? 'Ty' : 'Asystent'}:</strong> ${text}`;
        chatbox.appendChild(message);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage('user', text);
        userInput.value = "";

        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const data = await response.json();
        addMessage('assistant', data.response);
    }

    async function sendDiagnosis() {
        const response = await fetch("/diagnose", {
            method: "POST"
        });

        const data = await response.json();
        addMessage('assistant', data.response);
    }

    sendBtn.addEventListener("click", sendMessage);
    diagnoseBtn.addEventListener("click", sendDiagnosis);
});
