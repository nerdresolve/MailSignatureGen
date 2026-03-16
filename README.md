# Gerador de Assinaturas NerdResolve

## Requisitos

- **Node.js** 16+
- **Python 3** com o pacote `Pillow`:
  ```
  pip install Pillow
  ```

### Instalação rápida (Windows)
```
SignatureGeneratorRun.bat
```

### Instalação manual
```bash
npm install
pip install Pillow
node projeto/server.js
```

Acesse: http://localhost:3000

## Como funciona

1. Selecione o **segmento** (NerdResolve / Servicos / Offshore / Bunker-Estaleiro)
2. Preencha os dados (Nome, Setor, E-mail, Telefone)
3. Baixe a assinatura em PNG

## Dependências

Apenas **Pillow** (Python) + **Express** (Node.js). Não requer LibreOffice.
