# Reconhecimento de Placas Veiculares (100% Client-Side)

Aplicação web em arquivo único (`index.html`) que executa detecção de placas veiculares (incluindo Mercosul) e OCR dos caracteres utilizando **ONNX Runtime Web** com aceleração WebAssembly (Wasm).

## Arquitetura e Modelos

1. **Detecção (YOLOv8)**:
   - Pré-processamento com Letterboxing ($640 \times 640$) e normalização $[0, 1]$.
   - Pós-processamento com conversão de coordenadas para o canvas original e **NMS (Non-Maximum Suppression)**.
   - Desenho da Bounding Box e score no `<canvas>`.

2. **OCR (CRNN + Decodificação CTC)**:
   - Recorte da região da placa no canvas e redimensionamento proporcional ($168 \times 48$).
   - Normalização em tensores NCHW.
   - Algoritmo de **Greedy Search CTC** em JavaScript puro com eliminação de tokens duplicados e remoção de blanks para reconstrução dos caracteres.

## Como Baixar os Modelos e Executar

1. **Baixar os Modelos ONNX**:
```bash
npm run download:models
# ou diretamente:
node download_models.js
```

2. **Servir a Aplicação Web**:
```bash
npm start
# ou:
npx serve .
```

Abra `http://localhost:3000` (ou a porta informada pelo `serve`) no navegador, carregue a imagem ou use a câmera para detectar e reconhecer placas.

# plate-detection
