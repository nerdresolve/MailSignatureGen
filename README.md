# Gerador de Assinaturas — NerdResolve

Aplicação web para geração de assinaturas de e-mail em PNG para os segmentos do NerdResolve. O usuário seleciona o segmento, preenche os dados pessoais e faz o download da assinatura pronta para uso em clientes de e-mail.

---

## Segmentos disponíveis

| Segmento | Empresa |
|---|---|
| Corporativo | NerdResolve |
| Offshore | NerdResolve Offshore |
| Operacoes | Operacoes |
| Estaleiro | NerdResolve Estaleiro |
| Servicos | Servicos |

---

## Dependências

### Runtime

| Dependência | Versão mínima | Uso |
|---|---|---|
| [Node.js](https://nodejs.org/) | 16.x | Servidor web (Express) |
| [Python](https://www.python.org/) | 3.8+ | Geração de imagem (Pillow) |
| [Pillow](https://pypi.org/project/Pillow/) | 10.0.0+ | Manipulação de imagens PNG |
| [Express](https://expressjs.com/) | 4.x | Framework HTTP |

### Instalação das dependências

```bash
# Node.js
npm install

# Python
pip install -r requirements.txt
```

---

## Deploy local

### Windows

Execute o arquivo `.bat` na raiz do projeto:

```
SignatureGeneratorRun.bat
```

### Linux (Debian/Ubuntu)

```bash
chmod +x SignatureGeneratorRun.sh
./SignatureGeneratorRun.sh
```

Em ambos os casos o script irá:
1. Verificar se Node.js e Python estão instalados
2. Instalar as dependências automaticamente
3. Iniciar o servidor na porta 3000
4. Abrir o navegador em `http://localhost:3000` (se disponível)

#### Instalação de dependências no Debian 13

```bash
# Node.js 20.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Python e pip
sudo apt install -y python3 python3-pip
```

---

## Deploy manual (qualquer OS)

```bash
# 1. Instalar dependências
npm install
pip install -r requirements.txt

# 2. Iniciar o servidor
npm start
# ou
node projeto/server.js
```

Acesse: **http://localhost:3000**

---

## Deploy em produção

### Variáveis de ambiente

Nenhuma variável de ambiente obrigatória. A porta padrão é `3000` e pode ser alterada diretamente em `projeto/server.js`.

### Usando PM2 (recomendado para Linux/servidor)

```bash
npm install -g pm2
pm2 start projeto/server.js --name "assinatura-NerdResolve"
pm2 save
pm2 startup
```

### Usando systemd (Linux)

Crie o arquivo `/etc/systemd/system/assinatura-NerdResolve.service`:

```ini
[Unit]
Description=Gerador de Assinaturas NerdResolve
After=network.target

[Service]
WorkingDirectory=/caminho/para/MailSignatureGenV2
ExecStart=/usr/bin/node projeto/server.js
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable assinatura-NerdResolve
systemctl start assinatura-NerdResolve
```

### Proxy reverso com Nginx

```nginx
server {
    listen 80;
    server_name assinatura.suaempresa.com.br;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Estrutura do projeto

```
MailSignatureGenV2/
├── projeto/
│   ├── public/
│   │   ├── assets/          # Templates PNG e recursos estáticos
│   │   └── index.html       # Interface web (Tailwind CSS)
│   ├── server.js            # Servidor Express
│   └── signaturegenerator.py # Motor de geração de imagem (Pillow)
├── package.json
├── requirements.txt
├── SignatureGeneratorRun.bat # Inicialização rápida (Windows)
└── pyrightconfig.json       # Configuração do Pylance/Pyright
```

---

## Como funciona

1. O usuário acessa a interface web e seleciona o segmento da empresa
2. Preenche nome, setor, e-mail e telefone (opcional)
3. O front-end envia os dados via `POST /signaturegenerator`
4. O servidor Node.js valida os inputs e chama o script Python como subprocesso
5. O script Python abre o template PNG do segmento, sobrepõe os textos com Pillow e retorna a imagem via stdout
6. O servidor envia a imagem PNG como download direto no navegador

---

## Créditos

Desenvolvido por **[mariathdev](https://github.com/mariathdev)**.

---

## Licença

Uso interno — NerdResolve. Todos os direitos reservados.
