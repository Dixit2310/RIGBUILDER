/**
 * Futuristic Premium PC Assembly Page Loader Timeline Handler
 * Script controls SVG drop-in sequences, synthesized beep audio, progress updates, and exits.
 */
(function() {
    // 1. Session Storage Optimization: Skip full assembly load on subsequent page navigations
    const hasLoaded = sessionStorage.getItem("rigbuilder_loaded");
    const loader = document.getElementById("futuristic-loader");
    
    if (!loader) return;
    
    if (hasLoaded) {
        // Already loaded in this session: bypass full loader instantly to prevent navigation lag
        loader.style.display = "none";
        return;
    }
    
    // First page load: trigger full assembly animation timeline
    const progressBar = document.getElementById("loader-progress-bar");
    const percentage = document.getElementById("loader-percentage");
    const statusText = document.getElementById("loader-status");
    
    // Retrieve interactive component nodes
    const parts = {
        cpu: document.getElementById("part-cpu"),
        ram: document.getElementById("part-ram"),
        ssd: document.getElementById("part-ssd"),
        gpu: document.getElementById("part-gpu"),
        cooler: document.getElementById("part-cooler"),
        cables: document.getElementById("part-cables")
    };
    
    // Steps mapping (Timeline progress percentages, message logs, and animations)
    const steps = [
        { progress: 0, text: "Initializing Hardware...", action: () => {} },
        { progress: 12, text: "Checking Compatibility...", action: () => {} },
        { progress: 24, text: "Installing Processor...", action: () => parts.cpu.classList.remove("hidden") },
        { progress: 38, text: "Installing Memory...", action: () => parts.ram.classList.remove("hidden") },
        { progress: 50, text: "Installing Storage...", action: () => parts.ssd.classList.remove("hidden") },
        { progress: 64, text: "Installing Graphics Card...", action: () => parts.gpu.classList.remove("hidden") },
        { progress: 78, text: "Installing Cooling System...", action: () => {
            parts.cooler.classList.remove("hidden");
            parts.cooler.classList.add("fan-spinning");
        }},
        { progress: 88, text: "Connecting Power...", action: () => parts.cables.classList.remove("hidden") },
        { progress: 95, text: "Booting System...", action: () => {} },
        { progress: 100, text: "Your Dream PC is Ready.", action: () => {} }
    ];
    
    let currentStepIndex = 0;
    let progressVal = 0;
    
    // Web Audio Synthesized Motherboard Beeps (No external asset requests)
    let audioCtx = null;
    function playBeep(frequency, duration) {
        try {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            const osc = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            osc.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            osc.frequency.value = frequency;
            
            // Soft and clean motherboard sound volume profile
            gainNode.gain.setValueAtTime(0.04, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
            
            osc.start();
            osc.stop(audioCtx.currentTime + duration);
        } catch (e) {
            // Silence failures if audio context permissions block autoplay initially
            console.debug("Web Audio blocked by client autoplay policy.");
        }
    }
    
    // Incremental progress loop (Complete sequence takes approx ~3.8 seconds)
    const timer = setInterval(() => {
        progressVal += 1;
        percentage.innerText = `${progressVal}%`;
        progressBar.style.width = `${progressVal}%`;
        
        // Check if we hit the threshold to execute the next assembly step
        const nextStep = steps[currentStepIndex + 1];
        if (nextStep && progressVal >= nextStep.progress) {
            currentStepIndex++;
            statusText.innerText = steps[currentStepIndex].text;
            steps[currentStepIndex].action();
            
            // Trigger synthesized mother board installation beep
            if (steps[currentStepIndex].text.includes("Installing") || steps[currentStepIndex].text.includes("Connecting")) {
                playBeep(880, 0.07); // Short high pitch chip beep
            } else if (steps[currentStepIndex].text.includes("Ready")) {
                // Success system chime (C5 to E5 notes)
                playBeep(523.25, 0.25);
                setTimeout(() => playBeep(659.25, 0.35), 90);
            }
        }
        
        if (progressVal >= 100) {
            clearInterval(timer);
            
            // Smooth exit transition sequence
            setTimeout(() => {
                loader.classList.add("fade-away");
                // Set session marker to bypass loader on local page clicks
                sessionStorage.setItem("rigbuilder_loaded", "true");
                
                setTimeout(() => {
                    loader.style.display = "none";
                }, 800);
            }, 800);
        }
    }, 38);
})();
