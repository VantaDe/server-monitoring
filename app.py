import psutil
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request, Response
import speedtest

app = Flask(__name__)

stats = {
    "cpu_percent": 0.0,
    "ram_used_gb": 0.0,
    "ram_total_gb": 0.0,
    "ssd_percent": 0.0,
    "uptime_seconds": 0,
    "last_speedtest": "Nicht ausgeführt",
    "download_mbps": 0.0,
    "upload_mbps": 0.0,
    "speedtest_running": False,
    "net_in_bytes": 0,
    "net_out_bytes": 0,
}

start_time = time.time()
net_last = psutil.net_io_counters()

def update_stats():
    global net_last
    while True:
        stats["cpu_percent"] = psutil.cpu_percent(interval=1)
        vm = psutil.virtual_memory()
        stats["ram_used_gb"] = round((vm.total - vm.available) / (1024**3), 2)
        stats["ram_total_gb"] = round(vm.total / (1024**3), 2)
        
        try:
            stats["ssd_percent"] = psutil.disk_usage('/').percent
        except Exception:
            stats["ssd_percent"] = 0.0
        
        stats["uptime_seconds"] = int(time.time() - start_time)

        net_now = psutil.net_io_counters()
        stats["net_in_bytes"] = net_now.bytes_recv - net_last.bytes_recv
        stats["net_out_bytes"] = net_now.bytes_sent - net_last.bytes_sent
        net_last = net_now

        time.sleep(3)

def do_speedtest():
    stats["speedtest_running"] = True
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download()
        upload = st.upload()
        stats["download_mbps"] = round(download / 1_000_000, 2)
        stats["upload_mbps"] = round(upload / 1_000_000, 2)
        stats["last_speedtest"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print("Speedtest Fehler:", e)
        stats["download_mbps"] = 0.0
        stats["upload_mbps"] = 0.0
        stats["last_speedtest"] = "Fehler"
    finally:
        stats["speedtest_running"] = False

def format_uptime(seconds: int) -> str:
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return f"{int(d)}d {int(h)}h {int(m)}m {int(s)}s"

@app.route("/")
def index():
    html = """
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Server-Monitoring</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
    body {
        font-family: 'Poppins', sans-serif;
        background: #1a1a1a;
        color: #e0e0e0;
        margin: 0;
        padding: 40px 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
        overflow-x: hidden;
    }
    h1 {
        font-size: 3rem;
        color: #6a89cc;
        margin-bottom: 30px;
        text-shadow: 0 0 10px rgba(106, 137, 204, 0.4);
    }
    .status-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 25px;
        width: 100%;
        max-width: 1200px;
        margin-bottom: 40px;
    }
    .status-card {
        background: #252525;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
    }
    .status-card h3 {
        margin-top: 0;
        font-size: 1.5rem;
        color: #87cefa;
    }
    .status-card p {
        margin: 10px 0;
        font-size: 1.1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .status-card p strong {
        color: #e0e0e0;
    }
    .progress-bar-container {
        height: 12px;
        background: #34495e;
        border-radius: 6px;
        margin-top: 5px;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        border-radius: 6px;
        transition: width 0.7s ease-out;
    }
    .progress-bar.cpu { background: linear-gradient(90deg, #e74c3c, #c0392b); }
    .progress-bar.ram { background: linear-gradient(90deg, #2ecc71, #27ae60); }
    .progress-bar.ssd { background: linear-gradient(90deg, #f1c40f, #f39c12); }

    .chart-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
        gap: 25px;
        width: 100%;
        max-width: 1200px;
        margin-bottom: 40px;
    }
    .chart-card {
        background: #252525;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .chart-card h3 {
        margin-top: 0;
        font-size: 1.5rem;
        color: #87cefa;
    }
    canvas {
        width: 100% !important;
        height: 250px !important;
    }
    
    .button-container {
        margin-top: 20px;
        text-align: center;
    }
    .button-container button {
        background: linear-gradient(45deg, #6a89cc, #4a69bd);
        color: #fff;
        border: none;
        padding: 15px 30px;
        font-size: 1.1rem;
        font-weight: 700;
        border-radius: 50px;
        cursor: pointer;
        transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .button-container button:hover:not(:disabled) {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        background: linear-gradient(45deg, #4a69bd, #6a89cc);
    }
    .button-container button:disabled {
        background: #34495e;
        cursor: not-allowed;
        box-shadow: none;
    }

    footer {
        font-size: 0.9rem;
        color: #777;
        margin-top: auto;
        padding-top: 20px;
    }
</style>
</head>
<body>
    <h1>Server-Monitoring</h1>

    <div class="status-container">
        <div class="status-card">
            <h3>Systeminformationen</h3>
            <p><strong>CPU-Auslastung:</strong> <span id="cpu-text">--%</span></p>
            <div class="progress-bar-container"><div id="cpu-bar" class="progress-bar cpu"></div></div>
            <p><strong>RAM-Auslastung:</strong> <span id="ram-text">-- GiB</span> / <span id="ram-total-text">-- GiB</span></p>
            <div class="progress-bar-container"><div id="ram-bar" class="progress-bar ram"></div></div>
            <p><strong>SSD-Auslastung:</strong> <span id="ssd-text">--%</span></p>
            <div class="progress-bar-container"><div id="ssd-bar" class="progress-bar ssd"></div></div>
            <p><strong>Uptime:</strong> <span id="uptime-text">--</span></p>
        </div>
        <div class="status-card">
            <h3>Netzwerkinformationen</h3>
            <p><strong>Letzter Speedtest:</strong> <span id="speedtest-time-text">--</span></p>
            <p><strong>Download:</strong> <span id="download-text">-- Mbps</span></p>
            <p><strong>Upload:</strong> <span id="upload-text">-- Mbps</span></p>
            <div class="button-container">
                <button id="speedtest-btn">Speedtest starten</button>
            </div>
        </div>
    </div>

    <div class="chart-container">
        <div class="chart-card">
            <h3>CPU-Auslastung (%)</h3>
            <canvas id="cpuChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>RAM-Auslastung (GiB)</h3>
            <canvas id="ramChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Eingehender Traffic (Bytes)</h3>
            <canvas id="netInChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Ausgehender Traffic (Bytes)</h3>
            <canvas id="netOutChart"></canvas>
        </div>
    </div>
    
    <footer>Developed by vHosting</footer>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        const ramCtx = document.getElementById('ramChart').getContext('2d');
        const netInCtx = document.getElementById('netInChart').getContext('2d');
        const netOutCtx = document.getElementById('netOutChart').getContext('2d');

        const createChart = (ctx, label, color) => {
            return new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: label,
                        data: [],
                        borderColor: color,
                        backgroundColor: `${color}33`,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: {
                    animation: { duration: 600 },
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#e0e0e0' }
                        },
                        x: { display: false }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        };

        const cpuChart = createChart(cpuCtx, 'CPU %', '#e74c3c');
        const ramChart = createChart(ramCtx, 'RAM (GiB)', '#2ecc71');
        const netInChart = createChart(netInCtx, 'Incoming (Bytes)', '#f1c40f');
        const netOutChart = createChart(netOutCtx, 'Outgoing (Bytes)', '#8e44ad');

        function updateDisplay(id, value, unit) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = `${value}${unit}`;
            }
        }
        
        function updateProgressBar(id, percent) {
            const bar = document.getElementById(id);
            if (bar) bar.style.width = percent + "%";
        }

        async function refreshData() {
            try {
                const res = await fetch('/api/stats');
                if (!res.ok) throw new Error("Fehler beim Laden der Daten");
                const data = await res.json();
                
                // Update all system stats
                updateDisplay("cpu-text", data.cpu_percent.toFixed(2), "%");
                updateProgressBar("cpu-bar", data.cpu_percent);

                updateDisplay("ram-text", data.ram_used_gb.toFixed(2), " GiB");
                updateDisplay("ram-total-text", data.ram_total_gb.toFixed(2), " GiB");
                updateProgressBar("ram-bar", (data.ram_used_gb / data.ram_total_gb) * 100);

                updateDisplay("ssd-text", data.ssd_percent.toFixed(2), "%");
                updateProgressBar("ssd-bar", data.ssd_percent);

                document.getElementById("uptime-text").textContent = data.uptime_seconds;

                // Update charts
                const time = new Date().toLocaleTimeString();
                const maxDataPoints = 20;

                const addData = (chart, label, value) => {
                    chart.data.labels.push(label);
                    chart.data.datasets[0].data.push(value);
                    if (chart.data.labels.length > maxDataPoints) {
                        chart.data.labels.shift();
                        chart.data.datasets[0].data.shift();
                    }
                    chart.update();
                };

                addData(cpuChart, time, data.cpu_percent);
                addData(ramChart, time, data.ram_used_gb);
                addData(netInChart, time, data.net_in_bytes);
                addData(netOutChart, time, data.net_out_bytes);
                
                // Check speedtest status independently
                const btn = document.getElementById('speedtest-btn');
                if (data.speedtest_running) {
                    btn.disabled = true;
                    btn.textContent = "Speedtest läuft...";
                    document.getElementById("speedtest-time-text").textContent = "Läuft...";
                    document.getElementById("download-text").textContent = "-- Mbps";
                    document.getElementById("upload-text").textContent = "-- Mbps";
                } else {
                    btn.disabled = false;
                    btn.textContent = "Speedtest starten";
                    
                    updateDisplay("download-text", data.download_mbps, " Mbps");
                    updateDisplay("upload-text", data.upload_mbps, " Mbps");
                    document.getElementById("speedtest-time-text").textContent = data.last_speedtest;
                }

            } catch (e) {
                console.error("Fehler beim Abrufen der Daten:", e);
                const btn = document.getElementById('speedtest-btn');
                btn.disabled = false;
                btn.textContent = "Speedtest starten";
            }
        }
        
        const btn = document.getElementById('speedtest-btn');
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            btn.textContent = "Speedtest startet...";
            
            document.getElementById("download-text").textContent = "-- Mbps";
            document.getElementById("upload-text").textContent = "-- Mbps";
            document.getElementById("speedtest-time-text").textContent = "Läuft...";

            try {
                const res = await fetch('/api/speedtest', { method: 'POST' });
                if (!res.ok) throw new Error("Speedtest konnte nicht gestartet werden.");
                
            } catch (e) {
                console.error("Fehler beim Starten des Speedtests:", e);
                btn.textContent = "Fehler!";
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = "Speedtest starten";
                }, 3000);
            }
        });

        setInterval(refreshData, 5000);
        refreshData();
    </script>
</body>
</html>
"""
    return Response(html, mimetype='text/html')

@app.route("/api/stats")
def api_stats():
    result = stats.copy()
    result["uptime_seconds"] = format_uptime(stats["uptime_seconds"])
    return jsonify(result)

@app.route("/api/speedtest", methods=["POST"])
def api_speedtest():
    if stats["speedtest_running"]:
        return jsonify({"status": "running"}), 409
    thread = threading.Thread(target=do_speedtest, daemon=True)
    thread.start()
    return jsonify({"status": "started"})

if __name__ == "__main__":
    threading.Thread(target=update_stats, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)