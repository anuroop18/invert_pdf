import fitz
import sys
from PIL import Image
import io

def invert_pdf(input_path, output_path=None):
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '_inverted.pdf'
    
    # Open input PDF
    doc = fitz.open(input_path)
    # Create new PDF for output
    out_doc = fitz.open()
    
    for page in doc:
        # Convert page to high-res PNG image (300 DPI)
        zoom = 3  # higher zoom = higher quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(alpha=False, matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Invert the image
        img = Image.eval(img, lambda x: 255 - x)
        
        # Convert back to PDF page with high quality
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=False, quality=100)
        img_bytes.seek(0)
        
        # Add new page to output PDF
        new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)
    
    # Save with high quality settings
    out_doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    out_doc.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_inverter.py <input_pdf_path> [output_pdf_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    invert_pdf(input_path, output_path) 