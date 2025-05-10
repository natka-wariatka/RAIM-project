document.addEventListener("DOMContentLoaded", () => {
    const socket = io(); // Connect to the server
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const diagnoseBtn = document.getElementById("diagnoseBtn");
    const chatbox = document.getElementById("chatbox");

    // Funkcja dodawania wiadomości do czatu
    function addMessage(role, text) {
        const message = document.createElement("div");
        message.classList.add("mb-3");

        // Dostosowanie klasy do roli i wyglądu wiadomości
        message.classList.add(role === 'user' ? 'text-end' : 'text-start');
        message.innerHTML = `
            <div class="d-inline-block p-2 rounded-3 ${role === 'user' ? 'bg-success text-light' : 'bg-light text-dark'}">
                <strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> ${text}
            </div>
        `;
        chatbox.appendChild(message);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    // Obsługa przycisku wysyłania wiadomości
    sendBtn.addEventListener("click", () => {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage("user", text);
        socket.emit("user_message", { text });
        userInput.value = "";
    });

    // Obsługa przycisku diagnozy
    diagnoseBtn.addEventListener("click", () => {
        socket.emit("diagnose_request");
    });

    // Odbiór odpowiedzi od bota
    socket.on("bot_response", (data) => {
        addMessage("assistant", data.response);
    });

    // Obsługa Enter do wysyłania wiadomości
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendBtn.click();
    });
});
