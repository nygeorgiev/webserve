const lightMode = {
    "--background": "#ffffff",
    "--smooth": "#333333",
    "--scrollbar": "#f1f1f1"
}

const darkMode = {
    "--background": "#333333",
    "--smooth": "#bcbcbc",
    "--scrollbar": "#444444"
}

var currentMode = (typeof config != 'undefined') ? config['mode'] : 'light';

const setMode = (mode) => {
    if (mode != 'light' && mode != 'dark') return;
    theme = mode == 'light' ? lightMode : darkMode;
    let root = document.documentElement;
    for (let key in theme) {
        root.style.setProperty(key, theme[key])
    }
    currentMode = mode;
}

const changeMode = () => {
    let newMode = currentMode == 'light' ? 'dark' : 'light';
    setMode(newMode)
}

const isAtBottom = () => {
    const threshold = 30;
    return window.scrollHeight - window.scrollTop - window.clientHeight < threshold;
}

const init = () => {
    setMode(currentMode);
    const defaultModelTitle = "WebServe Model"
    const model = (typeof config != 'undefined') ? config['model'] : defaultModelTitle;
    const modelLabel = document.getElementById("model-name");
    modelLabel.innerText = model;
    if (model != defaultModelTitle) {
        document.title = `WebServe | ${model}`
    }
}