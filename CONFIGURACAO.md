# Configurar uma marca

Como colocar a sua empresa no gerador: criar a pasta, apontar o logo, escolher
as cores e decidir o que aparece na assinatura.

Uma **marca** é um diretório em `brands/` com um `brand.json` e as imagens que
ele cita. O código não sabe o nome de nenhuma empresa: ele lê aquele arquivo.
Trocar de cliente é criar uma pasta, e nada mais.

```
brands/
  nerdresolve/          a marca que acompanha o repositório, como exemplo
    brand.json
    logo.png
  suaempresa/           a sua
    brand.json
    logo.png
```

---

## O que você precisa antes de começar

| Item | Formato | Onde consegue |
|---|---|---|
| Logo | PNG com fundo transparente, ~500×60 | Manual de marca. Só o logotipo, sem margem sobrando |
| Cor da marca | Hexadecimal de 6 dígitos | Manual de marca. **Uma** cor |
| Domínio de e-mail | `suaempresa.com` | O que vai no *placeholder* do formulário |
| Redes sociais | Perfil e endereço | Opcional; sem elas a coluna do meio some |
| Lista de cargos | Texto | Opcional; vira sugestão no formulário |

Não há tela de administração, e é deliberado: criar uma marca é uma operação de
implantação, não do dia a dia.

---

## 1. Criar a pasta

```bash
mkdir brands/suaempresa
cp brands/nerdresolve/brand.json brands/suaempresa/brand.json
cp caminho/para/seu-logo.png brands/suaempresa/logo.png
```

O nome da pasta é o **id** da marca. Minúsculo, sem espaço nem acento: ele
aparece na linha de comando e na URL (`?marca=suaempresa`).

---

## 2. Editar o `brand.json`

O arquivo inteiro, comentado campo a campo:

```jsonc
{
  "nome": "Sua Empresa",              // aparece no título da página
  "site": "suaempresa.com",
  "dominioEmail": "suaempresa.com",   // placeholder do campo de e-mail

  "cores": {
    "marca":      "#7C3AED",          // nome, ícones, slogan e a faixa
    "texto":      "#1E1B2E",          // o cargo
    "textoSuave": "#6B7280",          // e-mail e telefone
    "fundo":      "#FFFFFF",
    "linha":      "#E5E7EB"           // o filete ao lado do slogan
  },

  "logo": {
    "arquivo": "logo.png",            // relativo a esta pasta
    "altura": 26                      // em pixels; a largura segue a proporção
  },

  "assinatura": {
    "largura": 800,
    "altura": 260,                    // mínimo, não teto — veja abaixo
    "margem": 32,
    "faixa": "onda"                   // "onda" | "barra" | "nenhuma"
  },

  "tipografia": {
    "nome":    { "peso": "bold",     "tamanho": 24, "cor": "marca", "caixaAlta": true },
    "cargo":   { "peso": "semibold", "tamanho": 15, "cor": "texto" },
    "contato": { "peso": "regular",  "tamanho": 14, "cor": "textoSuave" },
    "slogan":  { "peso": "semibold", "tamanho": 13, "cor": "marca" }
  },

  "slogan": "Uma frase curta.",       // "" remove o bloco e o filete

  "sociais": [
    { "rede": "site",      "handle": "suaempresa.com" },
    { "rede": "instagram", "handle": "@suaempresa" },
    { "rede": "linkedin",  "handle": "/company/suaempresa" }
  ],

  "perfis": [
    { "id": "padrao", "nome": "Sua Empresa", "descricao": "Assinatura institucional" }
  ],

  "cargos": ["Desenvolvedor", "Designer", "Comercial"],

  "telefone": { "obrigatorio": false }
}
```

### Os campos que merecem explicação

**`cores.marca`** é a única cor que quase sempre muda. Ela pinta o nome da
pessoa, os ícones das redes, o slogan e a faixa do topo — e também a interface
web, que se repinta ao carregar. As outras quatro raramente precisam de ajuste.

**`assinatura.altura` é um mínimo, não um teto.** Um nome comprido quebra em
duas linhas e empurra o conteúdo para baixo; nesse caso a imagem sai alguns
pixels mais alta, em vez de ter a última linha cortada. Se todas as suas
assinaturas saem maiores do que você quer, o caminho é reduzir `tipografia`, não
`altura`.

**`logo.altura`** é o que controla o tamanho do logo — a largura vem da
proporção do arquivo. Um logo que parece grande demais quase sempre está com
margem transparente sobrando; recorte-a antes.

**`faixa`** é o traço decorativo do topo:

| Valor | O que desenha |
|---|---|
| `onda` | Duas senoides na cor da marca. É o padrão |
| `barra` | Uma tarja reta de 6 px |
| `nenhuma` | Nada; o conteúdo sobe |

**`sociais[].rede`** aceita `site`, `instagram` e `linkedin`. Os ícones são
desenhados a traço pelo próprio gerador, então não há arquivo de imagem para
providenciar. Uma rede desconhecida recebe o ícone de globo.

**`tipografia.*.cor`** aponta para um nome declarado em `cores`, não para um
hexadecimal. Assim uma troca de paleta não deixa uma cor solta para trás.

---

## 3. Ver o resultado

```bash
python -m app.cli --marca suaempresa \
  --nome "Ana Souza" --cargo "Desenvolvedora" \
  --email "ana@suaempresa.com" --saida previa.png
```

Ou pela interface, que já traz a sua marca:

```bash
npm start
# http://localhost:3000?marca=suaempresa
```

Para tornar a sua marca a padrão, sem precisar da URL:

```bash
BRAND=suaempresa npm start
```

---

## Mais de uma marca na mesma instalação

Cada pasta em `brands/` é uma marca, e todas convivem. É o caso de quem atende
vários clientes, ou de um grupo com submarcas.

```bash
python -m app.cli --listar
```

A interface troca de marca pela URL (`?marca=<id>`), e `GET /api/marcas` lista
as instaladas — o suficiente para montar um seletor, se você quiser um.

### Perfis: variações dentro da mesma marca

Quando as unidades compartilham o layout mas mudam a cor ou o logo, use
**perfis** em vez de marcas separadas:

```jsonc
"perfis": [
  { "id": "corporativo", "nome": "Corporativo",  "descricao": "Matriz" },
  { "id": "industria",   "nome": "Indústria",    "cor": "#0F766E" },
  { "id": "servicos",    "nome": "Serviços",     "cor": "#B45309", "logo": "logo-servicos.png" }
]
```

Um perfil herda tudo da marca e sobrepõe o que declarar. Com mais de um perfil,
a interface mostra um seletor; com um só, ele não aparece.

---

## Trocar a fonte

A Manrope acompanha o repositório sob **SIL Open Font License**, que permite
redistribuição — inclusive num fork comercial. A licença está em
[`assets/fonts/OFL.txt`](assets/fonts/OFL.txt).

Para usar outra família, ponha três TTFs em `assets/fonts/` e ajuste o mapa
`PESOS` em [`app/brand.py`](app/brand.py):

```python
PESOS = {
    "regular":  "SuaFonte-Regular.ttf",
    "semibold": "SuaFonte-SemiBold.ttf",
    "bold":     "SuaFonte-Bold.ttf",
}
```

Confira a licença antes: nem toda fonte pode ser redistribuída num repositório
público.

---

## Quando algo não sai como esperado

O gerador recusa configuração inválida citando o campo, não um erro de Python.

| Mensagem | O que houve |
|---|---|
| `cores.marca: 'roxo' não é hexadecimal de seis dígitos` | Use `#7C3AED`; nome de cor e `rgb()` não valem |
| `logo.arquivo: não encontrado em …` | O caminho é relativo à pasta da marca |
| `perfis[0]: falta o campo 'id'` | Todo perfil precisa de `id` |
| `tipografia.nome.cor: 'roxinho' não é uma cor declarada` | A cor tem de existir em `cores` |
| `brand.json não é JSON válido: linha 12` | Quase sempre uma vírgula sobrando |
| `marca 'x' não encontrada (há: …)` | O id é o nome da pasta |

O texto sai maior ou menor do que o pedido quando não cabe: nome e cargo
encolhem até 85% e, se ainda assim não couberem, quebram em duas linhas. Nada é
truncado — é o nome de uma pessoa.

---

## Checklist

- [ ] `brands/<id>/brand.json` e `logo.png` no lugar
- [ ] `nome`, `cores.marca` e `dominioEmail` preenchidos
- [ ] Logo sem margem transparente sobrando
- [ ] `python -m app.cli --marca <id> --nome "Teste" --cargo "Cargo" --email "t@x.com" --saida previa.png`
- [ ] A prévia conferida num cliente de e-mail de verdade
- [ ] `npm test` passando
