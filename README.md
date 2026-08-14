# Reconhecimento de Placas Veiculares (FastAPI + PaddleOCR + Docker)

Aplicação full-stack para detecção e leitura de placas veiculares (incluindo o padrão Mercosul brasileiro e o padrão cinza antigo) utilizando **PaddleOCR** no backend containerizado em Docker e frontend web em HTML/CSS/JavaScript.

## Estrutura do Projeto

```
plate-detection/
├── api/
│   ├── Dockerfile            # Container Python 3.10-slim com OpenCV e PaddleOCR
│   ├── requirements.txt      # Dependências Python da API
│   └── main.py               # API FastAPI com endpoint POST /detect
├── docker-compose.yml        # Orquestração do container da API
├── index.html                # Frontend web interativo
├── package.json              # Scripts para servir o frontend
└── README.md                 # Documentação
```

---

## Como Executar

### 1. Iniciar o Backend (Docker)

No terminal da raiz do projeto, execute:

```bash
docker compose up --build
```

A API estará disponível em `http://localhost:8000` (documentação interativa Swagger em `http://localhost:8000/docs`).

### 2. Abrir o Frontend

Abra o arquivo [`index.html`](index.html) no navegador ou inicie um servidor local:

```bash
npm start
# ou
npx serve .
```

Envie qualquer foto de veículo com placa para visualizar a demarcação no canvas e o texto decodificado.
