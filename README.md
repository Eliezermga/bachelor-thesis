# Bachelor's thesis

This repository contains a thesis on the development of a machine translation system for a low-resource language and a LaTeX thesis template based on the `classicthesis` style. It is designed for a general audience to understand the structure and quickly build the final PDF from the source files.

## Project Overview

This thesis focuses on the development of a Neural Machine Translation system for low-resource languages, with a particular application to the **Ruund--French** language pair. Ruund is a Bantu language spoken mainly in the DRC and Angola, which suffers from a crucial lack of digital resources.

The main contributions of this project include:
- The construction of [**OpenRuund**](https://huggingface.co/datasets/eliezermga/OpenRuund), a parallel Ruund--French dataset (corpus).
- The experimentation and evaluation of various pre-trained multilingual neural translation models.
- The development of [**LugaYetu**](https://github.com/Eliezermga/Lugayetu), an application integrating the translation model as well as a linguistic data collection system.

## What is included

- `main.tex` — the main document entry point.
- `classicthesis-config.tex` — template configuration and metadata.
- `frontmatter/` — title pages, abstract, dedication, acknowledgments, and other front matter.
- `chapters/` — chapter content files.
- `bibliography/References.bib` — bibliography data.
- `annexes/` — appendices.
- `classicthesis.sty` — style file used by the template.

## Requirements

To use this template, you need a TeX distribution installed on your computer, for example:

- TeX Live (recommended on Linux)
- MiKTeX (Windows)
- MacTeX (macOS)

You also need a LaTeX build tool such as `latexmk` and the usual LaTeX packages used by the classicthesis template.

## How to install

1. Clone the repository:

   ```bash
   git clone https://github.com/Eliezermga/memoire.git
   cd memoire
   ```

2. Make sure your TeX distribution is installed and up to date.
3. Install or verify the following tools are available:
   - `pdflatex`
   - `bibtex8` or `bibtex`
   - `latexmk`

If you do not have `latexmk`, install it from your TeX distribution or package manager.

## How to build the thesis

From the repository root, run the build command:

```bash
latexmk -pdf main.tex
```

If `latexmk` is not available, you can build manually:

```bash
pdflatex main.tex
bibtex8 main
pdflatex main.tex
pdflatex main.tex
```

This will generate the output file `main.pdf`.

## How to customize

- Change the main title, author, and university details in `classicthesis-config.tex`.
- Edit chapter content in the files under `chapters/`.
- Edit the front matter content in `frontmatter/`.
- Update references in `bibliography/References.bib`.

## Output

The final compiled document is `main.pdf`.

## Notes

- `main.tex` is the main entry file for the thesis.
- `classicthesis-config.tex` contains the template settings and document metadata.
- The template is written in English and French, but you can change the language settings in the source files.
