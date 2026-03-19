/**
 * Theme Manager - Cursor Only Version (No Palette)
 * Just the cursor effects, no theme selector
 */

class ThemeManager {
    constructor() {
        this.initCursorEffects();
    }

    initCursorEffects() {
        // Only on desktop
        if (window.innerWidth <= 768) return;
        
        // Remove any existing cursor elements first
        const existingCursors = document.querySelectorAll('.cursor-dot, .cursor-glow, .cursor-trail, .cursor-trail-2');
        existingCursors.forEach(el => el.remove());
        
        // Create cursor elements
        this.createCursorElements();
        
        // Track mouse
        this.setupMouseTracking();
        
        console.log('✅ Cursor initialized');
    }

    createCursorElements() {
        // Dot cursor
        const dot = document.createElement('div');
        dot.className = 'cursor-dot';
        dot.style.cssText = `
            position: fixed;
            width: 20px;
            height: 20px;
            background: white;
            border: 3px solid #9333ea;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 20px #9333ea;
            transition: width 0.2s, height 0.2s;
        `;
        document.body.appendChild(dot);
        this.dot = dot;

        // Glow effect
        const glow = document.createElement('div');
        glow.className = 'cursor-glow';
        glow.style.cssText = `
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(147,51,234,0.2) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9998;
            transform: translate(-50%, -50%);
            filter: blur(40px);
        `;
        document.body.appendChild(glow);
        this.glow = glow;
    }

    setupMouseTracking() {
        let mouseX = 0, mouseY = 0;
        
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        const updateCursor = () => {
            if (this.dot && this.glow) {
                this.dot.style.left = mouseX + 'px';
                this.dot.style.top = mouseY + 'px';
                this.glow.style.left = mouseX + 'px';
                this.glow.style.top = mouseY + 'px';
            }
            requestAnimationFrame(updateCursor);
        };
        
        updateCursor();
    }
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}