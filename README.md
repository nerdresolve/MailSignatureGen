<div align="center">

<img src="docs/brand/banner.svg" alt="MailSignatureGen: brand-configurable email signature generator" width="100%">

An email signature generator your team runs on its own.
Each person fills in four fields and downloads the PNG; nobody opens Photoshop.

[![License](https://img.shields.io/badge/license-MIT-7C3AED)](LICENSE.md) ![Tests](https://img.shields.io/badge/tests-43%20passing-A78BFA) ![Stack](https://img.shields.io/badge/Python%203.10+-Node%2018+-1B1035) ![Dependencies](https://img.shields.io/badge/dependencies-2-5B21B6)

[The screens](#the-screens) · [How it works](#how-it-works) · [Running it](#running-it) · [Configure your brand](CONFIGURATION.md) · [License](#license)

</div>

---

## What this is

Every company that standardizes its email signature ends up in the same place: a
`.psd` on the drive, a ticket to the design team for every new hire, and three
different versions in circulation at once.

Here the signature is **drawn by code** from a configuration file. New people
fill in name, job title, email and phone, and get the finished PNG. Whoever owns
the brand edits a JSON file and swaps the logo — and everyone's signature
changes with it.

The repository ships with the **NerdResolve** brand as a working example. It is
the model to copy, not something to delete.

<div align="center">
<img src="docs/telas/02-previa.webp" alt="The interface with a generated signature" width="88%">
</div>

---

## How it works

There is no image template. The signature is composed from scratch on every
request, and that is what makes it configurable:

```
brands/yourcompany/brand.json    colors, typography, social links, profiles
brands/yourcompany/logo.png      the logo, and nothing else
         │
         ▼
  app/brand.py       validates and resolves: color becomes RGB, path becomes absolute
         │
         ▼
  app/render.py      stacks the blocks and draws with Pillow
         │
         ▼
  assinatura.png     800×260, ~40 kB
```

### Three decisions worth recording

**No flattened template.** The previous version opened a finished PNG, painted
white rectangles over the data of whoever had posed as the example, and rewrote
the text on top. It worked, at two costs: switching clients meant an image
editor and a fresh set of coordinates, and the PNG carried a real person's name,
email and phone into the repository. Drawing from scratch solves both at once.

**Height is a floor, not a ceiling.** A long name shrinks to 85% and, if it
still does not fit, wraps onto two lines — and the image grows to accommodate
it. Truncating is not an option: it is a person's name. There is a test
measuring that nothing is drawn outside the visible area, because Pillow clips
silently.

**Social icons are drawn as strokes**, not loaded from an icon font. The
previous version used Font Awesome over a CDN, which resolves in HTML and never
reaches Pillow — and an email signature needs the image, not the page. It is
~40 lines of geometry, and the project needs no network access to generate.

---

## The screens

<table>
<tr>
<td width="50%"><a href="docs/telas/01-formulario.webp"><img src="docs/telas/01-formulario.webp" alt="The form"></a><br><sub><b>Form</b> · four fields, and the job title offers suggestions</sub></td>
<td width="50%"><a href="docs/telas/02-previa.webp"><img src="docs/telas/02-previa.webp" alt="The signature preview"></a><br><sub><b>Preview</b> · the final image, before downloading</sub></td>
</tr>
</table>

<div align="center">
<a href="docs/telas/03-celular.webp"><img src="docs/telas/03-celular.webp" alt="The interface on a phone" width="30%"></a><br><sub><b>On a phone</b> · the same screen, in one column</sub>
</div>

> These are not mockups: it is the running application. `python tools/shots.py`
> starts the server, opens each screen in Chromium and saves what appears.

The interface paints itself with the colors of the loaded brand. Changing
`cores.marca` in the JSON changes the signature **and** the page.

---

## Running it

You need **Python 3.10+** and **Node 18+**.

```bash
npm run setup          # installs the dependencies on both sides
npm start              # http://localhost:3000
```

On Windows, `SignatureGeneratorRun.bat` does both steps and opens the browser.
On Linux and macOS, `./SignatureGeneratorRun.sh`.

### Without starting a server

The command line generates directly, which is useful for batches from a CSV:

```bash
python -m app.cli --nome "Ana Souza" --cargo "Desenvolvedora" \
  --email "ana.souza@nerdresolve.com" --telefone "+55 (21) 99999-9999" \
  --saida ana.png
```

```bash
python -m app.cli --listar        # the installed brands
```

### The tests

```bash
npm test               # 43 tests, all offline
```

They cover what the configuration accepts and rejects, and the properties of the
drawing: the contracted size, ink staying inside the usable area, text not
spilling into the neighboring column.

---

## Configure your brand

The step by step is in **[CONFIGURATION.md](CONFIGURATION.md)**. The short
version:

```bash
mkdir brands/yourcompany
cp brands/nerdresolve/brand.json brands/yourcompany/brand.json
cp your-logo.png brands/yourcompany/logo.png
# edit the JSON: name, colors, social links
BRAND=yourcompany npm start
```

What you can change without touching code:

| | |
|---|---|
| **Colors** | One brand color paints the name, icons, tagline, banner strip — and the interface |
| **Logo** | A PNG and the desired height; width follows the aspect ratio |
| **Typography** | Weight, size and color of each field |
| **Top strip** | `onda`, `barra` or `nenhuma` |
| **Social links** | Website, Instagram, LinkedIn — or none |
| **Profiles** | Color and logo variations within the same brand |
| **Job titles** | The list that becomes suggestions in the form |

Invalid configuration is rejected with the field named (`cores.marca: 'roxo' não
é hexadecimal de seis dígitos`), not with a Python traceback.

---

## Under the hood

```
app/
  brand.py         reads and validates brand.json; returns resolved values
  render.py        the drawing: strip, logo, three text columns, icons
  cli.py           command line, and what the server calls
  server.js        Express: serves the interface and exposes /api
  public/          the interface, HTML with no framework
brands/
  nerdresolve/     the example brand
assets/fonts/      Manrope (SIL Open Font License)
tests/             43 tests
tools/shots.py     the screenshots in this README
docs/              banner and screens
```

The server does not know how to draw: it validates the input and calls the CLI.
That way the layout lives in one place, instead of having a Python version and a
JavaScript version to keep in agreement.

### Architecture choices

| Decision | Why |
|---|---|
| **Pillow, not a headless browser** | A Chromium to draw 800×260 costs ~400 MB and a few seconds of startup. Pillow does it in ~200 ms with one dependency |
| **Python draws, Node serves** | Each does what it is already good at. The price is one subprocess per request — irrelevant at this scale |
| **The font ships with the repository** | A signature that depends on a system font comes out different on every machine. Manrope is OFL: it can be redistributed |
| **No database** | Nothing is stored. What a person types becomes an image and goes away |
| **Interface without a framework** | A four-field form does not justify a build step. It is HTML served directly |

---

## Known gaps

- **The preview is the final image.** There is no interactive editing: to adjust,
  change the field and generate again.
- **Three social networks.** `site`, `instagram` and `linkedin` have their own
  icon; anything else gets the globe. Adding one means writing the geometry in
  `_icone_social`.
- **No HTML output.** The signature is a PNG. An HTML version with clickable
  links would be better in some email clients, and does not exist yet.
- **One layout only.** Columns, order and positions are fixed; what changes is
  color, typography, logo and content. A second arrangement would take code.

---

## License

**MIT.** See [LICENSE.md](LICENSE.md). Use, modify and distribute it, including
commercially.

The license covers the code. The **NerdResolve** brand — the name, the logo and
the files in `brands/nerdresolve/` — is not included: when you use this project,
replace it with your own. Manrope has its own license, the
[SIL OFL](assets/fonts/OFL.txt), which permits redistribution.

---

<div align="center">

<img src="docs/brand/mark.png" alt="" width="52">

Built by [NerdResolve](https://nerdresolve.com)

Need something like this at your company? **contact@nerdresolve.com**

</div>
