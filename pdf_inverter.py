import fitz
import sys
from PIL import Image
import io
from tqdm import tqdm
import os
from multiprocessing import Pool
from functools import partial

def process_chunk(chunk_info, input_path, output_dir):
    start, end = chunk_info
    # Include input filename in temp filename
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    chunk_pdf = os.path.join(output_dir, f'temp_{base_name}_chunk_{start}_{end}.pdf')
    
    # Process chunk
    doc = fitz.open(input_path)
    out_doc = fitz.open()
    
    # Simple progress print instead of tqdm for subprocess
    print(f"Processing {base_name} pages {start}-{end}")
    
    for page_num in range(start, end):
        page = doc[page_num]
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
    
    out_doc.save(chunk_pdf, garbage=4, deflate=True)
    doc.close()
    out_doc.close()
    print(f"Completed {base_name} pages {start}-{end}")
    return chunk_pdf

def process_in_chunks(input_path, output_path=None, chunk_size=20):
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '_inverted.pdf'
    
    # Create temp directory inside current directory
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(input_path)), f'temp_{base_name}')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        doc = fitz.open(input_path)
        total_pages = doc.page_count
        doc.close()

        # Calculate optimal chunk size based on total pages
        if total_pages > 1000:
            chunk_size = 10  # Even smaller chunks for very large PDFs
        elif total_pages > 500:
            chunk_size = 15  # Medium chunks for large PDFs
        else:
            chunk_size = 20  # Default for regular PDFs

        print(f"\nInverting colors in {input_path}")
        print(f"Total pages: {total_pages}")
        print(f"Processing in chunks of {chunk_size} pages using 4 cores")
        print(f"Temporary files stored in: {temp_dir}")
        print("\nProgress:")
        
        # Prepare chunks
        chunks = [(i, min(i + chunk_size, total_pages)) 
                 for i in range(0, total_pages, chunk_size)]
        
        # Process chunks in parallel using exactly 4 cores
        with Pool(4) as pool:
            process_func = partial(process_chunk, input_path=input_path, output_dir=temp_dir)
            chunks_processed = []
            
            # Main progress bar for chunks
            with tqdm(total=len(chunks), desc=f"Overall progress ({base_name})", unit="chunk") as pbar:
                for result in pool.imap(process_func, chunks):
                    chunks_processed.append(result)
                    pbar.update(1)
        
        # Merge all chunks
        print(f"\nMerging processed chunks for {base_name}...")
        result_doc = fitz.open()
        chunk_files = sorted(chunks_processed)
        
        with tqdm(total=len(chunk_files), desc=f"Merging {base_name}") as pbar:
            for chunk_file in chunk_files:
                chunk_doc = fitz.open(chunk_file)
                result_doc.insert_pdf(chunk_doc)
                chunk_doc.close()
                os.remove(chunk_file)
                pbar.update(1)
        
        print(f"\nSaving final PDF to {output_path}")
        result_doc.save(output_path, garbage=4, deflate=True)
        result_doc.close()
        print("Done!")
        
    except Exception as e:
        print(f"Error processing {base_name}: {e}")
        raise e
    finally:
        # Clean up temp directory
        try:
            if os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, f))
                    except:
                        pass
                os.rmdir(temp_dir)
        except:
            print(f"Warning: Could not clean up temp directory: {temp_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_inverter.py <input_pdf_path> [output_pdf_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    process_in_chunks(input_path, output_path)