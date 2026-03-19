/**
 * Cursor Manager - Premium Edition
 * Custom cursor effects only — theme selector removed.
 */

class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        this.initCursorEffects();
    }

    initCursorEffects() {
        // Custom cursor only on desktop
        if (window.innerWidth <= 768) return;

        // Clean up any stale cursor elements from previous init
        document.querySelectorAll(
            '.cursor-dot, .cursor-glow, .cursor-trail, .cursor-trail-2'
        ).forEach(el => el.remove());

        // ── Create cursor elements ──────────────────────────────────────────
        const cursorGlow = document.createElement('div');
        cursorGlow.className = 'cursor-glow';

        const cursorDot = document.createElement('div');
        cursorDot.className = 'cursor-dot';

        const trail2 = document.createElement('div');
        trail2.className = 'cursor-trail-2';

        // Three shrinking trail dots
        const trails = Array.from({ length: 3 }, (_, i) => {
            const t = document.createElement('div');
            t.className = 'cursor-trail';
            const size = 10 - i * 2; // 10px → 8px → 6px
            t.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                opacity: ${0.6 - i * 0.15};
                z-index: ${2147483645 - i};
            `;
            return t;
        });

        // Append in z-order (glow lowest, dot highest)
        [cursorGlow, trail2, ...trails, cursorDot].forEach(el =>
            document.body.appendChild(el)
        );

        // ── State ───────────────────────────────────────────────────────────
        let mouseX = 0;
        let mouseY = 0;

        // Ring buffer for trail lag effect
        const TRAIL_DELAYS = [4, 8, 12];
        const TRAIL2_DELAY = 10;
        const BUFFER_SIZE  = 20;
        const posBuffer    = Array.from({ length: BUFFER_SIZE }, () => ({ x: 0, y: 0 }));
        let   bufferIndex  = 0;

        // ── Mouse tracking ──────────────────────────────────────────────────
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        // ── rAF animation loop ──────────────────────────────────────────────
        const tick = () => {
            posBuffer[bufferIndex] = { x: mouseX, y: mouseY };
            bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;

            // Position via left/top — CSS transform: translate(-50%,-50%) centres the dot
            cursorDot.style.left  = mouseX + 'px';
            cursorDot.style.top   = mouseY + 'px';

            cursorGlow.style.left = mouseX + 'px';
            cursorGlow.style.top  = mouseY + 'px';

            trails.forEach((trail, i) => {
                const idx = (bufferIndex - TRAIL_DELAYS[i] + BUFFER_SIZE) % BUFFER_SIZE;
                const pos = posBuffer[idx];
                trail.style.left = pos.x + 'px';
                trail.style.top  = pos.y + 'px';
            });

            const t2idx = (bufferIndex - TRAIL2_DELAY + BUFFER_SIZE) % BUFFER_SIZE;
            trail2.style.left = posBuffer[t2idx].x + 'px';
            trail2.style.top  = posBuffer[t2idx].y + 'px';

            requestAnimationFrame(tick);
        };

        requestAnimationFrame(tick);

        // ── Hover effects via event delegation ─────────────────────────────
        const INTERACTIVE = 'a, button, .card, .btn, .nav-link, .product-card, input, select, textarea, label';

        document.addEventListener('mouseover', (e) => {
            if (e.target.closest(INTERACTIVE)) {
                cursorDot.classList.add('hover');
                cursorGlow.classList.add('hover');
            }
        });

        document.addEventListener('mouseout', (e) => {
            if (e.target.closest(INTERACTIVE)) {
                cursorDot.classList.remove('hover');
                cursorGlow.classList.remove('hover');
            }
        });

        // ── Click burst ─────────────────────────────────────────────────────
        document.addEventListener('mousedown', () => {
            cursorDot.classList.add('click');
        });

        document.addEventListener('mouseup', () => {
            setTimeout(() => cursorDot.classList.remove('click'), 300);
        });

        // ── Handle window resize ────────────────────────────────────────────
        window.addEventListener('resize', () => {
            const hide = window.innerWidth <= 768;
            [cursorGlow, cursorDot, trail2, ...trails].forEach(el => {
                el.style.display = hide ? 'none' : '';
            });
            document.body.style.cursor = hide ? '' : 'none';
        });

        console.log('✅ Cursor initialised');
    }
}

// Initialise when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}