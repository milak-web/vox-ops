document.addEventListener("DOMContentLoaded", () => {
    
    // Smooth Scroll for Anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Intersection Observer for Animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.card, .stat-item').forEach(el => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = "opacity 0.6s ease-out, transform 0.6s ease-out";
        observer.observe(el);
    });

    // Add Fade In Class Logic
    const style = document.createElement('style');
    style.innerHTML = `
        .fade-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);

    // Glitch Text Effect Randomizer
    const glitchText = document.querySelector('.glitch');
    if(glitchText) {
        setInterval(() => {
            glitchText.style.textShadow = `
                ${Math.random() * 4 - 2}px ${Math.random() * 4 - 2}px var(--primary),
                ${Math.random() * 4 - 2}px ${Math.random() * 4 - 2}px var(--secondary)
            `;
            setTimeout(() => {
                glitchText.style.textShadow = "2px 2px var(--secondary), -2px -2px var(--primary)";
            }, 100);
        }, 3000);
    }

    // Console Typer Effect
    const consoleLines = document.querySelectorAll('.terminal-body p');
    consoleLines.forEach((line, index) => {
        line.style.opacity = '0';
        setTimeout(() => {
            line.style.opacity = '1';
        }, index * 800);
    });

    // VOICE DEMO ANIMATION LOOP
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    const line1 = document.getElementById('line1');
    const line2 = document.getElementById('line2');

    // SCENARIO DATA
    const scenarios = [
        {
            voice: '"Engage Shields!"',
            action: 'SHIELDS UP',
            icon: 'fa-shield-alt'
        },
        {
            voice: '"Open Map!"',
            action: 'MAP OPENED',
            icon: 'fa-map-marked-alt'
        },
        {
            voice: '"Reload Weapon!"',
            action: 'RELOADING...',
            icon: 'fa-sync-alt'
        }
    ];

    let currentScenarioIndex = 0;

    if(step1 && step2 && step3) {
        function runDemo() {
            // Get current scenario data
            const scenario = scenarios[currentScenarioIndex];

            // Reset UI
            step1.classList.remove('active', 'success');
            step2.classList.remove('active', 'success');
            step3.classList.remove('active', 'success');
            line1.classList.remove('active');
            line2.classList.remove('active');

            // Update Text & Icons (Hidden initially)
            setTimeout(() => {
                // Update Voice Text
                step1.querySelector('.demo-text').textContent = scenario.voice;
                
                // Update Action Text & Icon
                step3.querySelector('.demo-text').textContent = scenario.action;
                const actionIcon = step3.querySelector('.demo-icon');
                actionIcon.className = `fas ${scenario.icon} demo-icon`;
            }, 100); // Small delay to allow reset to happen visually

            // Step 1: Speak
            setTimeout(() => {
                step1.classList.add('active');
            }, 500);

            // Step 2: Process
            setTimeout(() => {
                line1.classList.add('active');
                step1.classList.remove('active');
                step1.classList.add('success');
                step2.classList.add('active');
            }, 2000);

            // Step 3: Action
            setTimeout(() => {
                line2.classList.add('active');
                step2.classList.remove('active');
                step2.classList.add('success');
                step3.classList.add('active');
                step3.classList.add('success');
            }, 3500);

            // Prepare next scenario index
            currentScenarioIndex = (currentScenarioIndex + 1) % scenarios.length;

            // Loop
            setTimeout(runDemo, 6000);
        }
        
        runDemo();
    }

});