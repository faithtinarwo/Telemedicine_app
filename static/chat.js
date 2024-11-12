document.addEventListener("DOMContentLoaded", () => {
    const messageContainer = document.querySelector(".messages");
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const fileUpload = document.getElementById("fileUpload");
    const attachButton = document.getElementById("attachButton");
    const callButton = document.getElementById("callButton");
    const endConsultationButton = document.querySelector(".end-consultation");

    // Function to send patient message
    function sendMessage() {
        const messageText = messageInput.value.trim();
        
        if (messageText) {
            addMessage(messageText, 'patient');
            messageInput.value = ""; // Clear input box

            // Simulate a doctor’s response
            setTimeout(() => receiveMessage("I see. Could you elaborate more on that?"), 2000);
        }
    }

    // Function to add a message to the chat
    function addMessage(text, sender) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", `${sender}-message`);
        messageElement.innerHTML = `<p>${text}</p><span class="timestamp">${new Date().toLocaleTimeString()}</span>`;
        
        messageContainer.appendChild(messageElement);
        messageContainer.scrollTop = messageContainer.scrollHeight; // Auto-scroll to the latest message
    }

    // Function to display doctor’s response
    function receiveMessage(text) {
        addMessage(text, 'doctor');
    }

    // Function to initiate a call (placeholder functionality)
    function initiateCall() {
        alert("Calling the doctor...");
        // Here, you could add WebRTC or another video/audio call library.
    }

    // Handle file attachment
    attachButton.addEventListener("click", () => {
        fileUpload.click(); // Trigger the file input click
    });

    fileUpload.addEventListener("change", () => {
        const fileName = fileUpload.files[0]?.name;
        if (fileName) {
            addMessage(`📎 ${fileName}`, 'patient');
        }
    });

    // Initial greeting message
    receiveMessage("Good day, how can I help you?");

    // Event Listeners
    sendButton.addEventListener("click", sendMessage);
    messageInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
    callButton.addEventListener("click", initiateCall); // Call button functionality
    endConsultationButton.addEventListener("click", () => {
        alert("Consultation has ended.");
        window.location.href = "/"; // Redirect to the homepage or another page
    });
});


