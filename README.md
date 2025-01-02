# PDF Inverter

A Python tool to invert colors in PDF documents, making them easier to read in dark mode or for better contrast.

## Features

- Inverts colors in PDF documents while preserving text quality
- Maintains document structure and formatting
- Supports both single and multi-page PDFs

## Requirements

- Python 3.x
- Required packages (install via pip):
  ```
  uv sync
  ```

## Usage

Run the script with your PDF file:

```bash
python pdf_inverter.py input.pdf
```

The inverted PDF will be saved with "_inverted" suffix in the same directory.

## Example

Input: `example.pdf` → Output: `example_inverted.pdf`

## License

MIT License
