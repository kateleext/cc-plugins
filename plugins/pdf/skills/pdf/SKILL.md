---
name: "pdf"
description: "Generate beautifully styled PDFs from markdown content. Use when converting markdown to PDF, creating documents, or processing documentation folders. Supports multiple styles including minimal, corporate, technical, shokuna (dark mode), and newsletter."
---

# PDF Generator

Convert markdown to professionally styled PDFs.

## Setup (one-time)

```bash
pip install -r requirements.txt
```

Note: WeasyPrint requires system dependencies. On macOS:
```bash
brew install pango
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

## Usage

```bash
# From a file (outputs to same location as source.pdf by default)
pdf --input /path/to/doc.md --style minimal

# From a file with custom output
pdf --input /path/to/doc.md --output /path/to/output.pdf

# From inline markdown (--output required)
pdf --markdown "# Title\n\nContent" --output /path/to/output.pdf

# From a folder of markdown files (--output required)
pdf --folder /path/to/docs/ --output /path/to/combined.pdf

# List available styles
pdf --list-styles
```

## Styles

| Style | Best For |
|-------|----------|
| `minimal` | General docs, notes |
| `corporate` | Business documents |
| `technical` | API docs, specs |
| `shokuna` | Dark mode, brand |
| `newsletter` | Articles, essays |

## Options

| Option | Description |
|--------|-------------|
| `--input`, `-i` | Markdown file path |
| `--markdown`, `-m` | Inline markdown content |
| `--folder`, `-f` | Folder of markdown files |
| `--output`, `-o` | Output PDF path (optional for --input, defaults to source.pdf) |
| `--style`, `-s` | Style name (default: minimal) |
| `--css` | Custom CSS file |
| `--list-styles` | Show available styles |
