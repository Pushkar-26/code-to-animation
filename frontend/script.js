let selectedLanguage = "cpp";
let allFrames = [];
let currentStep = 0;
let isPlaying = false;
let playInterval = null;

const codeInput = document.getElementById("codeInput");
const traceBtn = document.getElementById("traceBtn");
const codeDisplay = document.getElementById("codeDisplay");
const errorDisplay = document.getElementById("errorDisplay");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const stepCounter = document.getElementById("stepCounter");
const callStackView = document.getElementById("callStackView");
const playBtn = document.getElementById("playBtn");
const languageSelect = document.getElementById("languageSelect");

// DEBUG: check ki elements sahi se mil rahe hain ya nahi
console.log("DEBUG - codeInput:", codeInput);
console.log("DEBUG - traceBtn:", traceBtn);
console.log("DEBUG - codeDisplay:", codeDisplay);
console.log("DEBUG - errorDisplay:", errorDisplay);
console.log("DEBUG - prevBtn:", prevBtn);
console.log("DEBUG - nextBtn:", nextBtn);
console.log("DEBUG - stepCounter:", stepCounter);
console.log("DEBUG - callStackView:", callStackView);
console.log("DEBUG - playBtn:", playBtn);
console.log("DEBUG - languageSelect:", languageSelect);

// Default C++ code set karo
codeInput.value = `#include <iostream>
using namespace std;

int main() {
    int x = 5;
    int y = 10;
    int z = x + y;
    return 0;
}`;

languageSelect.addEventListener("change", () => {
    selectedLanguage = languageSelect.value;
    console.log("DEBUG - language changed to:", selectedLanguage);
    if (selectedLanguage === "cpp") {
        codeInput.value = `#include <iostream>
using namespace std;

int main() {
    int x = 5;
    int y = 10;
    int z = x + y;
    return 0;
}`;
    } else {
        codeInput.value = `def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(4)`;
    }
    codeInput.style.display = "block";
    codeDisplay.style.display = "none";
    errorDisplay.style.display = "none";
    stopPlaying();
    allFrames = [];
    currentStep = 0;
    stepCounter.textContent = "Step 0 / 0";
    callStackView.innerHTML = "";
});

traceBtn.addEventListener("click", async () => {
    const code = codeInput.value.trim();

    if (!code) {
        alert("Please enter some code first!");
        return;
    }

    errorDisplay.style.display = "none";

    try {
        const response = await fetch("http://127.0.0.1:8001/trace", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code: code,
                language: selectedLanguage
            })
        });

        const text = await response.text();
        console.log("Raw Response:", text);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}\n${text}`);
        }

        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            throw new Error("Backend did not return valid JSON.\n\n" + text);
        }

        if (data.error) {
            errorDisplay.textContent = data.error;
            errorDisplay.style.display = "block";
            return;
        }

        allFrames = data.frames || [];
        currentStep = 0;

        if (allFrames.length === 0) {
            errorDisplay.textContent = "No frames generated.";
            errorDisplay.style.display = "block";
            return;
        }

        buildCodeDisplay(code);

        window.currentError = null;

        codeInput.style.display = "none";
        codeDisplay.style.display = "block";

        prevBtn.disabled = false;
        nextBtn.disabled = false;
        playBtn.disabled = false;

        renderStep();

    } catch (err) {
        console.error(err);

        errorDisplay.textContent = err.message;
        errorDisplay.style.display = "block";
    }
});

nextBtn.addEventListener("click", () => {
    if (currentStep < allFrames.length - 1) {
        currentStep++;
        renderStep();
    }
});

prevBtn.addEventListener("click", () => {
    if (currentStep > 0) {
        currentStep--;
        renderStep();
    }
});

playBtn.addEventListener("click", () => {
    if (isPlaying) {
        stopPlaying();
    } else {
        startPlaying();
    }
});

function startPlaying() {
    isPlaying = true;
    playBtn.textContent = "⏸ Pause";
    playInterval = setInterval(() => {
        if (currentStep < allFrames.length - 1) {
            currentStep++;
            renderStep();
        } else {
            stopPlaying();
        }
    }, 800);
}

function stopPlaying() {
    isPlaying = false;
    playBtn.textContent = "▶ Play";
    clearInterval(playInterval);
    playInterval = null;
}

function renderStep() {
    const frame = allFrames[currentStep];
    stepCounter.textContent = `Step ${currentStep + 1} / ${allFrames.length}`;
    callStackView.innerHTML = "";

    const output = frame.output || "";
    const outputPanel = document.getElementById("outputPanel");
    if (output) {
        outputPanel.textContent = output;
        outputPanel.style.display = "block";
    } else {
        outputPanel.style.display = "none";
    }

    frame.call_stack.forEach((stackFrame, index) => {
        const frameBox = document.createElement("div");
        frameBox.className = "frame-box";
        if (index === frame.call_stack.length - 1) {
            frameBox.classList.add("active");
        }

        const frameName = document.createElement("div");
        frameName.className = "frame-name";
        frameName.textContent = `${stackFrame.function_name}() — Line ${stackFrame.line_number}`;

        const frameVars = document.createElement("div");
        frameVars.className = "frame-vars";
        const varsText = Object.entries(stackFrame.locals)
            .map(([key, value]) => `${key} = ${JSON.stringify(value)}`)
            .join(" | ");
        frameVars.innerHTML = `<span>Variables:</span> ${varsText || "(none)"}`;

        frameBox.appendChild(frameName);
        frameBox.appendChild(frameVars);
        callStackView.appendChild(frameBox);
    });

    document.querySelectorAll(".code-line").forEach(line => {
        line.classList.remove("highlighted");
    });

    const currentLine = document.getElementById(`line-${frame.line_number}`);
    if (currentLine) {
        currentLine.classList.add("highlighted");
        currentLine.scrollIntoView({ block: "nearest" });
    }

    if (currentStep === allFrames.length - 1 && window.currentError) {
        errorDisplay.textContent = window.currentError;
        errorDisplay.style.display = "block";
    } else {
        errorDisplay.style.display = "none";
    }
}

function buildCodeDisplay(code) {
    codeDisplay.innerHTML = "";
    const lines = code.split("\n");
    lines.forEach((lineText, index) => {
        const lineDiv = document.createElement("div");
        lineDiv.className = "code-line";
        lineDiv.id = `line-${index + 1}`;
        lineDiv.textContent = lineText === "" ? " " : lineText;
        codeDisplay.appendChild(lineDiv);
    });
}