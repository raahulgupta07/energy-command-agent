"""
Mermaid diagram helper for rendering flowcharts in Streamlit.
Includes zoom in/out/reset controls + click-drag to pan.
"""

import streamlit as st
import streamlit.components.v1 as components
import hashlib


def render_mermaid(code: str, height: int = 500):
    """Render a Mermaid diagram with zoom + pan (drag to move) controls."""
    uid = "m_" + hashlib.md5(code.encode()).hexdigest()[:8]

    html = f"""
    <style>
        #{uid}_wrapper {{
            background: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
            user-select: none;
        }}
        #{uid}_toolbar {{
            display: flex;
            gap: 6px;
            padding: 8px 12px;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            align-items: center;
            flex-wrap: wrap;
        }}
        #{uid}_toolbar button {{
            background: white;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 4px 12px;
            cursor: pointer;
            font-size: 13px;
            color: #475569;
            transition: all 0.15s;
        }}
        #{uid}_toolbar button:hover {{
            background: #eff6ff;
            border-color: #3b82f6;
            color: #2563eb;
        }}
        #{uid}_toolbar .zoom-label {{
            font-size: 12px;
            color: #94a3b8;
            margin-left: auto;
            font-family: monospace;
        }}
        #{uid}_toolbar .hint {{
            font-size: 11px;
            color: #94a3b8;
            margin-left: 8px;
        }}
        #{uid}_viewport {{
            overflow: hidden;
            cursor: grab;
            position: relative;
            height: {height - 52}px;
        }}
        #{uid}_viewport:active {{
            cursor: grabbing;
        }}
        #{uid}_diagram {{
            transform-origin: 0 0;
            transition: none;
            position: absolute;
            top: 0;
            left: 0;
        }}
        #{uid}_diagram .mermaid {{
            text-align: center;
        }}
    </style>

    <div id="{uid}_wrapper">
        <div id="{uid}_toolbar">
            <button onclick="{uid}_zoomIn()">+ Zoom In</button>
            <button onclick="{uid}_zoomOut()">- Zoom Out</button>
            <button onclick="{uid}_reset()">Reset</button>
            <button onclick="{uid}_fit()">Fit</button>
            <span class="hint">Drag to pan</span>
            <span class="zoom-label" id="{uid}_label">100%</span>
        </div>
        <div id="{uid}_viewport">
            <div id="{uid}_diagram">
                <pre class="mermaid">
{code}
                </pre>
            </div>
        </div>
    </div>

    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                primaryColor: '#eff6ff',
                primaryTextColor: '#1e293b',
                primaryBorderColor: '#3b82f6',
                lineColor: '#64748b',
                secondaryColor: '#f0fdf4',
                tertiaryColor: '#fef2f2',
                fontFamily: 'Inter, system-ui, sans-serif',
                fontSize: '14px'
            }}
        }});

        const viewport = document.getElementById('{uid}_viewport');
        const diagram = document.getElementById('{uid}_diagram');
        const label = document.getElementById('{uid}_label');

        let scale = 1.0;
        let panX = 0;
        let panY = 0;
        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let startPanX = 0;
        let startPanY = 0;

        function applyTransform() {{
            diagram.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{scale}})`;
            label.textContent = Math.round(scale * 100) + '%';
        }}

        // Zoom buttons
        window.{uid}_zoomIn = function() {{
            scale = Math.min(scale + 0.2, 4.0);
            applyTransform();
        }};

        window.{uid}_zoomOut = function() {{
            scale = Math.max(scale - 0.2, 0.2);
            applyTransform();
        }};

        window.{uid}_reset = function() {{
            scale = 1.0;
            panX = 0;
            panY = 0;
            applyTransform();
        }};

        window.{uid}_fit = function() {{
            const svg = diagram.querySelector('svg');
            if (svg && viewport) {{
                const vw = viewport.clientWidth;
                const vh = viewport.clientHeight;
                const sw = svg.scrollWidth;
                const sh = svg.scrollHeight;
                scale = Math.min(vw / sw, vh / sh, 1.5) * 0.9;
                panX = Math.max(0, (vw - sw * scale) / 2);
                panY = 10;
                applyTransform();
            }}
        }};

        // Mouse drag to pan
        viewport.addEventListener('mousedown', function(e) {{
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            startPanX = panX;
            startPanY = panY;
            e.preventDefault();
        }});

        viewport.addEventListener('mousemove', function(e) {{
            if (!isDragging) return;
            panX = startPanX + (e.clientX - startX);
            panY = startPanY + (e.clientY - startY);
            applyTransform();
        }});

        viewport.addEventListener('mouseup', function() {{
            isDragging = false;
        }});

        viewport.addEventListener('mouseleave', function() {{
            isDragging = false;
        }});

        // Mouse wheel to zoom
        viewport.addEventListener('wheel', function(e) {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.1 : 0.1;
            scale = Math.min(Math.max(scale + delta, 0.2), 4.0);
            applyTransform();
        }}, {{ passive: false }});

        // Touch support for mobile
        let lastTouchDist = 0;
        let touchStartX = 0;
        let touchStartY = 0;

        viewport.addEventListener('touchstart', function(e) {{
            if (e.touches.length === 1) {{
                isDragging = true;
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                startPanX = panX;
                startPanY = panY;
            }} else if (e.touches.length === 2) {{
                isDragging = false;
                lastTouchDist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
            }}
            e.preventDefault();
        }}, {{ passive: false }});

        viewport.addEventListener('touchmove', function(e) {{
            if (e.touches.length === 1 && isDragging) {{
                panX = startPanX + (e.touches[0].clientX - touchStartX);
                panY = startPanY + (e.touches[0].clientY - touchStartY);
                applyTransform();
            }} else if (e.touches.length === 2) {{
                const dist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                if (lastTouchDist > 0) {{
                    scale = Math.min(Math.max(scale * (dist / lastTouchDist), 0.2), 4.0);
                    applyTransform();
                }}
                lastTouchDist = dist;
            }}
            e.preventDefault();
        }}, {{ passive: false }});

        viewport.addEventListener('touchend', function() {{
            isDragging = false;
            lastTouchDist = 0;
        }});

        // Center diagram after mermaid renders
        setTimeout(function() {{
            window.{uid}_fit();
        }}, 1500);
    </script>
    """
    components.html(html, height=height, scrolling=False)
