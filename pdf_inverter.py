import fitz
import sys
from PIL import Image
import io
from tqdm import tqdm

def invert_pdf(input_path, output_path=None):
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '_inverted.pdf'
    
    # Open input PDF
    doc = fitz.open(input_path)
    out_doc = fitz.open()
    
    print(f"\nInverting colors in {input_path}...")
    for page in tqdm(doc, desc="Processing pages", unit="page"):
        zoom = 3
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(alpha=False, matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = Image.eval(img, lambda x: 255 - x)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=False, quality=100)
        img_bytes.seek(0)
        
        new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)
    
    print(f"\nSaving to {output_path}...")
    out_doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    out_doc.close()
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_inverter.py <input_pdf_path> [output_pdf_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    invert_pdf(input_path, output_path)