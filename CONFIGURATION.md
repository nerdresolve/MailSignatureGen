# Configuring a brand

How to put your company into the generator: create the folder, point at the
logo, pick the colors and decide what appears in the signature.

A **brand** is a directory under `brands/` with a `brand.json` and the images it
references. The code does not know any company name: it reads that file.
Switching clients means creating a folder, and nothing more.

```
brands/
  nerdresolve/          the brand that ships with the repository, as an example
    brand.json
    logo.png
  yourcompany/          yours
    brand.json
    logo.png
```

---

## What you need before you start

| Item | Format | Where it comes from |
|---|---|---|
| Logo | PNG with a transparent background, ~500×60 | Brand guidelines. The logo only, with no leftover margin |
| Brand color | 6-digit hexadecimal | Brand guidelines. **One** color |
| Email domain | `yourcompany.com` | What goes in the form's *placeholder* |
| Social links | Profile and address | Optional; without them the middle column disappears |
| Job title list | Text | Optional; becomes suggestions in the form |

There is no admin screen, and that is deliberate: creating a brand is a
deployment operation, not a day-to-day one.

---

## 1. Create the folder

```bash
mkdir brands/yourcompany
cp brands/nerdresolve/brand.json brands/yourcompany/brand.json
cp path/to/your-logo.png brands/yourcompany/logo.png
```

The folder name is the brand **id**. Lowercase, no spaces or accents: it shows
up on the command line and in the URL (`?marca=yourcompany`).

---

## 2. Edit `brand.json`

The whole file, commented field by field:

```jsonc
{
  "nome": "Your Company",             // appears in the page title
  "site": "yourcompany.com",
  "dominioEmail": "yourcompany.com",  // placeholder for the email field

  "cores": {
    "marca":      "#7C3AED",          // name, icons, tagline and the strip
    "texto":      "#1E1B2E",          // the job title
    "textoSuave": "#6B7280",          // email and phone
    "fundo":      "#FFFFFF",
    "linha":      "#E5E7EB"           // the rule beside the tagline
  },

  "logo": {
    "arquivo": "logo.png",            // relative to this folder
    "altura": 26                      // in pixels; width follows the aspect ratio
  },

  "assinatura": {
    "largura": 800,
    "altura": 260,                    // a floor, not a ceiling — see below
    "margem": 32,
    "faixa": "onda"                   // "onda" | "barra" | "nenhuma"
  },

  "tipografia": {
    "nome":    { "peso": "bold",     "tamanho": 24, "cor": "marca", "caixaAlta": true },
    "cargo":   { "peso": "semibold", "tamanho": 15, "cor": "texto" },
    "contato": { "peso": "regular",  "tamanho": 14, "cor": "textoSuave" },
    "slogan":  { "peso": "semibold", "tamanho": 13, "cor": "marca" }
  },

  "slogan": "A short line.",          // "" removes the block and the rule

  "sociais": [
    { "rede": "site",      "handle": "yourcompany.com" },
    { "rede": "instagram", "handle": "@yourcompany" },
    { "rede": "linkedin",  "handle": "/company/yourcompany" }
  ],

  "perfis": [
    { "id": "padrao", "nome": "Your Company", "descricao": "Corporate signature" }
  ],

  "cargos": ["Developer", "Designer", "Sales"],

  "telefone": { "obrigatorio": false }
}
```

### The fields that deserve an explanation

**`cores.marca`** is the one color that almost always changes. It paints the
person's name, the social icons, the tagline and the top strip — and also the
web interface, which repaints itself on load. The other four rarely need
adjusting.

**`assinatura.altura` is a floor, not a ceiling.** A long name wraps onto two
lines and pushes the content down; in that case the image comes out a few pixels
taller, instead of having its last line cut off. If all your signatures come out
bigger than you want, the fix is to reduce `tipografia`, not `altura`.

**`logo.altura`** is what controls the logo size — the width comes from the
file's aspect ratio. A logo that looks too big almost always has leftover
transparent margin; crop it first.

**`faixa`** is the decorative stroke at the top:

| Value | What it draws |
|---|---|
| `onda` | Two sine waves in the brand color. This is the default |
| `barra` | A straight 6 px band |
| `nenhuma` | Nothing; the content moves up |

**`sociais[].rede`** accepts `site`, `instagram` and `linkedin`. The icons are
drawn as strokes by the generator itself, so there is no image file to supply.
An unknown network gets the globe icon.

**`tipografia.*.cor`** points at a name declared in `cores`, not at a hex value.
That way a palette change does not leave a stray color behind.

---

## 3. See the result

```bash
python -m app.cli --marca yourcompany \
  --nome "Ana Souza" --cargo "Desenvolvedora" \
  --email "ana@yourcompany.com" --saida previa.png
```

Or through the interface, which already carries your brand:

```bash
npm start
# http://localhost:3000?marca=yourcompany
```

To make your brand the default, without needing the URL:

```bash
BRAND=yourcompany npm start
```

---

## More than one brand in the same installation

Every folder under `brands/` is a brand, and they all coexist. That is the case
for anyone serving several clients, or for a group with sub-brands.

```bash
python -m app.cli --listar
```

The interface switches brands through the URL (`?marca=<id>`), and
`GET /api/marcas` lists the installed ones — enough to build a picker, if you
want one.

### Profiles: variations within the same brand

When units share the layout but differ in color or logo, use **profiles**
instead of separate brands:

```jsonc
"perfis": [
  { "id": "corporativo", "nome": "Corporate",  "descricao": "Headquarters" },
  { "id": "industria",   "nome": "Industrial", "cor": "#0F766E" },
  { "id": "servicos",    "nome": "Services",   "cor": "#B45309", "logo": "logo-servicos.png" }
]
```

A profile inherits everything from the brand and overrides whatever it declares.
With more than one profile, the interface shows a picker; with only one, it does
not appear.

---

## Changing the font

Manrope ships with the repository under the **SIL Open Font License**, which
permits redistribution — including in a commercial fork. The license is in
[`assets/fonts/OFL.txt`](assets/fonts/OFL.txt).

To use another family, put three TTFs in `assets/fonts/` and adjust the `PESOS`
map in [`app/brand.py`](app/brand.py):

```python
PESOS = {
    "regular":  "YourFont-Regular.ttf",
    "semibold": "YourFont-SemiBold.ttf",
    "bold":     "YourFont-Bold.ttf",
}
```

Check the license first: not every font can be redistributed in a public
repository.

---

## When something does not come out as expected

The generator rejects invalid configuration with the field named, not with a
Python traceback. The messages below are what it prints, verbatim:

| Message | What happened |
|---|---|
| `cores.marca: 'roxo' não é hexadecimal de seis dígitos` | Use `#7C3AED`; color names and `rgb()` are not accepted |
| `logo.arquivo: não encontrado em …` | The path is relative to the brand folder |
| `perfis[0]: falta o campo 'id'` | Every profile needs an `id` |
| `tipografia.nome.cor: 'roxinho' não é uma cor declarada` | The color has to exist in `cores` |
| `brand.json não é JSON válido: linha 12` | Almost always a trailing comma |
| `marca 'x' não encontrada (há: …)` | The id is the folder name |

Text comes out larger or smaller than requested when it does not fit: name and
job title shrink to 85% and, if they still do not fit, wrap onto two lines.
Nothing is truncated — it is a person's name.

---

## Checklist

- [ ] `brands/<id>/brand.json` and `logo.png` in place
- [ ] `nome`, `cores.marca` and `dominioEmail` filled in
- [ ] Logo with no leftover transparent margin
- [ ] `python -m app.cli --marca <id> --nome "Teste" --cargo "Cargo" --email "t@x.com" --saida previa.png`
- [ ] The preview checked in a real email client
- [ ] `npm test` passing
