const useMathJax = (typeof config != 'undefined') ? config['latex'] : false;

var messageHistory = [];
var sendingMessage = false;
var currentAssistantMessageContainer = null;
var stopSignal = false;

const scrollToBottom = () => {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

const nonStreamingButtons = () => {
    const jsonButton = document.getElementById("json-btn");
    const clearButton = document.getElementById("clear-btn");
    const stopButton = document.getElementById("stop-btn");
    jsonButton.style.display = "inline-block";
    clearButton.style.display = "inline-block";
    stopButton.style.display = "none";
}

const streamingButtons = () => {
    const jsonButton = document.getElementById("json-btn");
    const clearButton = document.getElementById("clear-btn");
    const stopButton = document.getElementById("stop-btn");
    jsonButton.style.display = "none";
    clearButton.style.display = "none";
    stopButton.style.display = "inline-block";
}

const isBottom = () => {
    const threshold = 10;
    return window.scrollHeight - window.scrollTop - window.clientHeight < threshold;
}

const createNewMessageWrapper = () => {
    const wrapper = document.createElement("div");
    const container = document.getElementById("messages");
    wrapper.setAttribute("class", "message-wrapper");
    container.appendChild(wrapper);
    return wrapper;
}

const addUserMessageBox = (text) => {
    const wasAtBottom = isBottom();
    const wrapper = createNewMessageWrapper();
    const element = document.createElement("div");
    element.setAttribute("class", "user-message");
    element.innerText = text;
    wrapper.appendChild(element);
    currentAssistantMessageContainer = null;
    if (wasAtBottom)
        scrollToBottom();
    if (useMathJax) {
        MathJax.typesetPromise([element]);
    }
}

const addAssistantMessageBox = () => {
    if (currentAssistantMessageContainer) 
        return;
    const wrapper = createNewMessageWrapper();
    const element = document.createElement("div");
    element.setAttribute("class", "assistant-message");
    wrapper.appendChild(element);
    currentAssistantMessageContainer = element;
}

const setAssistantMessage = (text, isError = false) => {
    const wasAtBottom = isBottom();
    if (!currentAssistantMessageContainer)
        addAssistantMessageBox();
    currentAssistantMessageContainer.innerText = text;
    if (isError) {
        currentAssistantMessageContainer.setAttribute("class", "assistant-message error-message");
    }
    if (wasAtBottom)
        scrollToBottom();
    if (useMathJax) {
        MathJax.typesetPromise([currentAssistantMessageContainer]);
    }
}

const sendMessage = () => {
    const input = document.getElementById("input-msg");
    const message = input.textContent;
    if (!message || sendingMessage) return;
    sendingMessage = true;
    streamingButtons();
    input.textContent = "";
    addUserMessageBox(message);

    messageHistory.push({
        "role": "user",
        "content": message
    });

    const loc = window.location;
    const wsProtocol = loc.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${loc.host}/v1/retrieveResponse`;
    const socket = new WebSocket(wsUrl);

    socket.addEventListener('open', () => {
        console.log('WebSocket connected.');
        socket.send(JSON.stringify(messageHistory));
    });

    socket.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
            setAssistantMessage(data.error, true)
        }

        if (data.output) {
            setAssistantMessage(data.output);
        }

        if (data.completed || stopSignal) {
            messageHistory.push({
                "role": "assistant",
                "content": data.output
            })
            socket.close(1000);
        }
    });

    socket.addEventListener("close", (event) => {
        console.log("Socket closed.")
        nonStreamingButtons();
        sendingMessage = false;
        stopSignal = false;
    })
}

const stopStreaming = () => {
    if (sendingMessage) {
        stopSignal = true;
    }
}

const askClearConfirm = () => {
    const popup = document.getElementById("confirm-popup")
    popup.style.display = "flex";
}

const clearChat = () => {
    const messagesContainer = document.getElementById("messages");
    messagesContainer.innerHTML = "";
    messageHistory = [];
    const jsonButton = document.getElementById("json-btn");
    const clearButton = document.getElementById("clear-btn");
    const stopButton = document.getElementById("stop-btn");
    jsonButton.style.display = "none";
    clearButton.style.display = "none";
    stopButton.style.display = "none";
    const popup = document.getElementById("confirm-popup")
    popup.style.display = "none";
}

const rejectClearChat = () => {
    const popup = document.getElementById("confirm-popup")
    popup.style.display = "none";
}

const downloadJSON = () => {
    const model = (typeof config != 'undefined') ? config['model'] : 'webserve'; 
    const temperature = (typeof config != 'undefined') ? config['temperature'] : null; 
    const slashIndex = model.indexOf("/");
    const provider = slashIndex === -1 ? model : model.slice(0, slashIndex);
    const filename = `${provider.toLowerCase()}-${Date.now().toString(36).slice(-8)}.json`;

    const data = {
        "model": model,
        "temperature": temperature,
        "messages": messageHistory
    }
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();

    // Clean up the object URL
    URL.revokeObjectURL(url);
}