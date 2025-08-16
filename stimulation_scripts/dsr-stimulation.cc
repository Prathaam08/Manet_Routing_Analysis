/* ===== GENERAL PAGE STYLES ===== */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
    color: #e4e4e4;
    margin: 0;
    padding: 0;
    min-height: 100vh;
}

/* ===== CONTROL PANEL ===== */
.control-panel {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.control-panel h2 {
    font-size: 1.6rem;
    color: #00c6ff;
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
    margin-bottom: 15px;
}

/* Labels & Inputs */
.form-label {
    font-weight: 600;
    color: #b0c4de;
}

.form-control, .form-select {
    border-radius: 8px;
    border: 1px solid #444;
    background: rgba(255,255,255,0.05);
    color: #fff;
    transition: all 0.2s ease;
}

.form-control:focus, .form-select:focus {
    border-color: #00c6ff;
    box-shadow: 0 0 8px rgba(0,198,255,0.6);
    background: rgba(255,255,255,0.08);
}

/* ===== BUTTONS ===== */
.btn {
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
    transition: all 0.25s ease;
    border: none;
}

.btn:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 6px 14px rgba(0,0,0,0.5);
}

.btn-info {
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: #fff;
}
.btn-success {
    background: linear-gradient(135deg, #28a745, #1e7e34);
    color: #fff;
}
.btn-danger {
    background: linear-gradient(135deg, #dc3545, #a71d2a);
    color: #fff;
}

/* ===== HISTORY LIST ===== */
.history-list {
    max-height: 220px;
    overflow-y: auto;
    border-radius: 10px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
}

.history-list .list-group-item {
    background: transparent;
    color: #ddd;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    transition: all 0.2s ease;
}
.history-list .list-group-item:hover {
    background-color: rgba(0,198,255,0.1);
    color: #00c6ff;
}

/* ===== CARDS ===== */
.card {
    border-radius: 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    color: #eee;
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.6);
}

.card-header {
    font-weight: 700;
    background: rgba(0,0,0,0.3);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    color: #00c6ff;
}

/* ===== NETWORK CANVAS ===== */
.network-canvas {
    height: 550px;
    background: rgba(0,0,0,0.25);
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: inset 0 0 15px rgba(0,198,255,0.3);
}

/* ===== CHARTS ===== */
.chart-card {
    height: 320px;          /* balanced height */
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
}

.chart-card canvas {
    width: 100% !important;
    height: 100% !important;
}



/* ===== CUSTOM NODE STYLE (for D3.js) ===== */
.network-node {
    stroke: #00c6ff;
    stroke-width: 2px;
    fill: #0072ff;
    transition: transform 0.2s ease;
}
.network-node:hover {
    fill: #28a745;
    stroke: #00ff9d;
    transform: scale(1.3);
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: #444;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #00c6ff;
}
