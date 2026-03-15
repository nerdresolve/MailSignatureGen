# Gerador de Assinaturas NerdResolve

Gerador de assinaturas de e-mail para os segmentos do NerdResolve.

## Requisitos

- **Node.js** 16+
- **Python 3** com os pacotes:
  - `python-pptx` → `pip install python-pptx`
- **LibreOffice** (para conversão PPTX → PDF)
- **Poppler** (`pdftoppm`, para conversão PDF → PNG)

### Instalação rápida (Windows)
```
SignatureGeneratorRun.bat
```

### Instalação manual
```bash
npm install
pip install python-pptx
node projeto/server.js
```

Acesse: http://localhost:3000

## Fluxo

1. **Selecione o segmento** (NerdResolve / Servicos / Offshore / Bunker-Estaleiro)
2. **Preencha os dados** (Nome, Setor, E-mail, Telefone)
3. **Baixe a assinatura** em PNG

## Segmentos disponíveis

| Segmento | Slide |
|----------|-------|
| NerdResolve / Corporativo | 1 |
| Servicos | 2 |
| Offshore | 3 |
| Bunker / Estaleiro | 4 |

> Os modelos estão em `projeto/public/assets/blankmodels.pptx`
