<?php
// capturar.php - Versão adaptada para Bookworm e rpicam-apps
header('Content-Type: image/jpeg');

$resolucao = isset($_GET['res']) ? $_GET['res'] : '1024x768';
list($width, $height) = explode('x', $resolucao);
$width = intval($width);
$height = intval($height);

// Define um arquivo temporário
$outputFile = '/tmp/camera_capture.jpg';

// Comando usando rpicam-jpeg (sucessor do raspistill)
// --nopreview: sem janela de prévia
// --timeout 500: captura após 500ms (dá tempo pro foco ajustar, pode reduzir para 100 ou 0 se quiser mais velocidade)
// --width / --height: define a resolução
// --quality 85: qualidade JPEG (quanto maior, mais qualidade mas mais demorado/pesado)
// --output: arquivo de saída
$cmd = "rpicam-jpeg --nopreview --timeout 500 --width {$width} --height {$height} --quality 85 --output " . escapeshellarg($outputFile) . " 2>&1";

// Executa o comando
exec($cmd, $output, $returnCode);

// Log para debug (opcional)
error_log("Comando executado: " . $cmd);
error_log("Código de retorno: " . $returnCode);

// Verifica se a imagem foi gerada
if ($returnCode !== 0 || !file_exists($outputFile) || filesize($outputFile) == 0) {
    http_response_code(500);
    echo "Erro ao capturar imagem. Código: " . $returnCode;
    if (!empty($output)) {
        echo "\nDetalhes: " . implode("\n", $output);
    }
    exit;
}

// Lê o arquivo e envia para o browser
readfile($outputFile);

// Limpeza: remove o arquivo temporário para não acumular lixo
@unlink($outputFile);
?>