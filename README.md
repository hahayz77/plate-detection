# Reconhecimento de Placas Veiculares (FastAPI + PaddleOCR + Docker)

Aplicação full-stack de alta precisão para detecção e leitura de placas veiculares brasileiras (incluindo o padrão **Mercosul** `LLLNLNN` e o padrão **antigo/cinza** `LLLNNNN`), utilizando **PaddleOCR** no backend conteinerizado com Docker e frontend web moderno em HTML5/Vanilla CSS/JavaScript.

---

## Sumário
- [Arquitetura e Recursos](#arquitetura-e-recursos)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pós-Processamento e Heurísticas Mercosul](#pós-processamento-e-heurísticas-mercosul)
- [Como Executar](#como-executar)
- [Especificação da API](#especificação-da-api)
- [Frontend e Interface de Testes](#frontend-e-interface-de-testes)
- [Solução de Problemas (Troubleshooting)](#solução-de-problemas-troubleshooting)

---

## Arquitetura e Recursos

1. **Backend em Container Docker (Python + FastAPI)**:
   - Baseado em imagem enxuta `python:3.10-slim`.
   - Motor OCR com **PaddleOCR 2.8.1** e **PaddlePaddle 2.6.2**, garantindo compatibilidade e estabilidade em CPU.
   - Endpoint assíncrono `POST /detect` para upload de imagens via `multipart/form-data`.
   - Conversão de cores RGB/BGR via OpenCV e extração de coordenadas e polígonos delimitadores da placa.

2. **Frontend Web Moderno e Responsivo (`index.html`)**:
   - Desenvolvido em HTML5, Vanilla CSS (Dark Theme) e JavaScript puro.
   - Monitoramento em tempo real do status da API (`/health`) com indicador visual (Ready/Working/Error).
   - Suporte a Drag-and-Drop de imagens e seletor de arquivos.
   - Renderização sobreposta no `<canvas>` destacando a caixa delimitadora (`bounding box`/polígono) com etiquetas de confiança.
   - Visualização com mockup estilizado no formato oficial da placa Mercosul.
   - Painel integrado de logs de execução e métricas de tempo de resposta em milissegundos.

---

## Estrutura do Projeto

```
plate-detection/
├── api/
│   ├── Dockerfile            # Configuração Docker com dependências de OpenCV e PaddleOCR
│   ├── requirements.txt      # Dependências Python travadas para estabilidade (FastAPI, PaddleOCR 2.8.1)
│   └── main.py               # API FastAPI com validações, correção e endpoint /detect
├── docker-compose.yml        # Orquestração do container (mapeamento 8000:8000 + healthcheck)
├── index.html                # Frontend web interativo para testes
├── package.json              # Configurações e scripts para inicialização do frontend
└── README.md                 # Documentação detalhada
```

---

## Pós-Processamento e Heurísticas Mercosul

O backend aplica uma camada inteligente de correção posicional em [`api/main.py`](api/main.py) baseada nas regras de formação das placas no Brasil:

- **Padrão Mercosul**: 3 Letras + 1 Número + 1 Letra + 2 Números (`[A-Z]{3}[0-9][A-Z][0-9]{2}`) — Ex: `BRA2E19`.
- **Padrão Antigo**: 3 Letras + 4 Números (`[A-Z]{3}[0-9]{4}`) — Ex: `ABC1234`.

### Correção Posicional de Caracteres Ambíguos:
Se o OCR confundir caracteres por semelhança visual:
- Em posições onde **obrigatoriamente deve haver uma letra** (ex: primeiras 3 posições): números comuns são convertidos (`0 -> O`, `1 -> I`, `2 -> Z`, `4 -> A`, `5 -> S`, `6 -> G`, `8 -> B`).
- Em posições onde **obrigatoriamente deve haver um número** (ex: 4ª, 6ª e 7ª posições): letras são convertidas para seus dígitos equivalentes (`O/D/Q -> 0`, `I/L -> 1`, `Z -> 2`, `A -> 4`, `S -> 5`, `G -> 6`, `B -> 8`).

---

## Como Executar

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose instalados.
- [Node.js](https://nodejs.org/) (opcional, para servir o frontend via `npm start`).

### 1. Iniciar o Backend no Docker
Na raiz do projeto, execute:

```bash
docker compose up --build
```

A API iniciará na porta `8000`:
- **API Base**: `http://localhost:8000`
- **Healthcheck**: `http://localhost:8000/health`
- **Documentação Swagger Interativa**: `http://localhost:8000/docs`

> **Dica para ver logs detalhados do build**:
> ```bash
> docker compose build --progress=plain
> ```

### 2. Iniciar o Frontend de Teste
Você pode abrir o [`index.html`](index.html) diretamente no seu navegador com duplo clique, ou iniciar um servidor web local com npm:

```bash
npm start
# ou:
npx serve .
```

Acesse o endereço exibido no terminal (ex: `http://localhost:3000`), envie uma imagem e visualize o resultado imediato.

---

## Especificação da API

### `POST /detect`
Recebe um arquivo de imagem e retorna as placas identificadas e metadados de inferência.

- **Content-Type**: `multipart/form-data`
- **Body**: `file` (arquivo de imagem JPG, PNG ou WEBP)

#### Exemplo de Resposta JSON:
```json
{
  "success": true,
  "image_width": 1280,
  "image_height": 720,
  "processing_time_ms": 142.5,
  "plates_count": 1,
  "plates": [
    {
      "raw_text": "BRA-2E19",
      "text": "BRA2E19",
      "confidence": 0.9854,
      "is_mercosul": true,
      "is_classic": false,
      "is_valid_plate": true,
      "box": {
        "x": 450,
        "y": 310,
        "width": 210,
        "height": 75,
        "polygon": [
          [450, 310],
          [660, 310],
          [660, 385],
          [450, 385]
        ]
      }
    }
  ],
  "all_detections": [ ... ]
}
```

---

## Solução de Problemas (Troubleshooting)

| Problema | Causa | Solução |
| :--- | :--- | :--- |
| `Unknown argument: show_log` | Incompatibilidade de sintaxe do PaddleOCR | Parâmetro descontinuado removido em `main.py`. |
| `AnalysisConfig object has no attribute 'set_optimization_level'` | Incompatibilidade entre PaddleOCR 3.x e PaddlePaddle 2.6.x | Fixada a versão estável `paddleocr==2.8.1` em `requirements.txt`. |
| Demora excessiva no build do Docker | Download de modelos em servidores internacionais durante o build | Pré-download removido da fase de build do Dockerfile; modelos são carregados pelo runtime. |
| Erro de CORS no frontend | Bloqueio de requisições cross-origin no navegador | Middleware `CORSMiddleware` com permissão total já habilitado no FastAPI. |
