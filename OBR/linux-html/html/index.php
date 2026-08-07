<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPi Zero 2W - Camera Controller</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            margin: 0;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            margin-bottom: 10px;
            color: #00ff88;
        }
        .status {
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .resolucao-select, button {
            padding: 12px 24px;
            font-size: 16px;
            margin: 10px;
            border-radius: 8px;
            cursor: pointer;
        }
        .resolucao-select {
            background: #333;
            color: white;
            border: 2px solid #00ff88;
        }
        button {
            background: #00ff88;
            color: #1a1a2e;
            border: none;
            font-weight: bold;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.05);
            background: #00ffaa;
        }
        .foto-container {
            background: #000;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        img {
            max-width: 100%;
            border-radius: 8px;
            display: none;
            border: 2px solid #00ff88;
        }
        .loading {
            color: #ffaa00;
            font-size: 18px;
        }
        .info {
            margin-top: 20px;
            font-size: 12px;
            color: #888;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
        }
        .stat-card {
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 8px;
            min-width: 100px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
        }
        .modal-content {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            margin: 20% auto;
            padding: 20px;
            border-radius: 15px;
            width: 300px;
            text-align: center;
        }
        .tempo-display {
            font-size: 48px;
            font-weight: bold;
            color: #00ff88;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📷 RPi Zero 2W - Camera</h1>
        
        <div class="status" id="status">
            ✅ Sistema pronto | Clique em "Tirar Foto"
        </div>
        
        <select id="resolucao" class="resolucao-select">
            <option value="640x480">VGA (640x480) - Mais Rápido</option>
            <option value="1024x768">XGA (1024x768) - Bom</option>
            <option value="1920x1080">Full HD (1920x1080)</option>
            <option value="2592x1944">5MP (2592x1944) - Alta Resolução</option>
            <option value="3280x2464">8MP (3280x2464) - Máxima</option>
        </select>
        
        <button onclick="tirarFoto()">📸 TIRAR FOTO</button>
        
        <div class="foto-container">
            <div id="loading" class="loading" style="display:none;">
                ⏳ Capturando imagem... Aguarde
            </div>
            <img id="foto" src="" alt="Última foto capturada">
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div>Melhor tempo</div>
                <div class="stat-value" id="bestTime">-- ms</div>
            </div>
            <div class="stat-card">
                <div>Último tempo</div>
                <div class="stat-value" id="lastTime">-- ms</div>
            </div>
        </div>
        
        <div class="info">
            💡 Dica: Resoluções menores capturam mais rápido<br>
            🔧 Raspberry Pi Zero 2W com câmera oficial
        </div>
    </div>
    
    <!-- Modal de tempo -->
    <div id="tempoModal" class="modal">
        <div class="modal-content">
            <h3>⏱️ TEMPO DE CAPTURA</h3>
            <div class="tempo-display" id="tempoDisplay">0 ms</div>
            <button onclick="fecharModal()" style="background:#00ff88; padding:8px 20px; border:none; border-radius:5px;">OK</button>
        </div>
    </div>
    
    <script>
        let bestTime = Infinity;
        
        function mostrarModal(tempoMs) {
            const modal = document.getElementById('tempoModal');
            const tempoDisplay = document.getElementById('tempoDisplay');
            tempoDisplay.textContent = tempoMs + ' ms';
            modal.style.display = 'block';
            setTimeout(() => fecharModal(), 2000);
        }
        
        function fecharModal() {
            document.getElementById('tempoModal').style.display = 'none';
        }
        
        function atualizarEstatisticas(tempo) {
            if (tempo < bestTime) {
                bestTime = tempo;
                document.getElementById('bestTime').innerHTML = bestTime + ' ms';
            }
            document.getElementById('lastTime').innerHTML = tempo + ' ms';
            
            let color = tempo < 1000 ? '#00ff88' : (tempo < 2000 ? '#ffaa00' : '#ff4444');
            document.getElementById('lastTime').style.color = color;
        }
        
        async function tirarFoto() {
            const resolucao = document.getElementById('resolucao').value;
            const loading = document.getElementById('loading');
            const img = document.getElementById('foto');
            const status = document.getElementById('status');
            
            const inicio = performance.now();
            
            loading.style.display = 'block';
            img.style.display = 'none';
            status.innerHTML = '⏳ Processando captura...';
            
            try {
                const response = await fetch(`/capturar.php?res=${encodeURIComponent(resolucao)}&t=${Date.now()}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);
                
                img.onload = () => {
                    URL.revokeObjectURL(imageUrl);
                    loading.style.display = 'none';
                    img.style.display = 'block';
                    
                    const fim = performance.now();
                    const tempo = Math.round(fim - inicio);
                    
                    atualizarEstatisticas(tempo);
                    mostrarModal(tempo);
                    status.innerHTML = `✅ Foto capturada em ${tempo}ms | Resolução: ${resolucao}`;
                };
                
                img.src = imageUrl;
                
            } catch (error) {
                loading.style.display = 'none';
                status.innerHTML = '❌ Erro ao capturar: ' + error.message;
                console.error('Erro:', error);
            }
        }
    </script>
</body>
</html>