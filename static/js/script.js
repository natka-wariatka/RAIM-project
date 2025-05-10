document.addEventListener("DOMContentLoaded", () => {
    const socket = io(); // Connect to the server
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const diagnoseBtn = document.getElementById("diagnoseBtn");
    const chatbox = document.getElementById("chatbox");

    function addMessage(role, text) {
        const message = document.createElement("div");
        message.classList.add(role);
        message.innerHTML = `<strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> ${text}`;
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

    socket.on("bot_response", (data) => {
        addMessage("assistant", data.response);
    });
});