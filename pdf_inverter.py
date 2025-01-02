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
    chunk_pdf = os.path.join(output_dir, f'temp_chunk_{start}_{end}.pdf')
    
    # Process chunk
    doc = fitz.open(input_path)
    out_doc = fitz.open()
    
    # Progress bar for pages within this chunk
    pbar = tqdm(range(start, end), 
                desc=f"Pages {start}-{end}",
                unit="page",
                leave=False,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} pages")
    
    for page_num in pbar:
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
    return chunk_pdf

def process_in_chunks(input_path, output_path=None, chunk_size=50):
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '_inverted.pdf'
    
    output_dir = os.path.dirname(os.path.abspath(input_path))
    
    try:
        doc = fitz.open(input_path)
        total_pages = doc.page_count
        doc.close()

        print(f"\nInverting colors in {input_path}")
        print(f"Total pages: {total_pages}")
        print(f"Processing in chunks of {chunk_size} pages using 4 cores")
        print("Progress:")
        
        # Prepare chunks
        chunks = [(i, min(i + chunk_size, total_pages)) 
                 for i in range(0, total_pages, chunk_size)]
        
        # Process chunks in parallel using exactly 4 cores
        with Pool(4) as pool:
            process_func = partial(process_chunk, input_path=input_path, output_dir=output_dir)
            chunk_bar = tqdm(total=len(chunks), 
                           desc="Chunks", 
                           unit="chunk",
                           position=0,
                           bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} chunks [{elapsed}<{remaining}]")
            
            chunks_processed = []
            for result in pool.imap(process_func, chunks):
                chunks_processed.append(result)
                chunk_bar.update(1)
            chunk_bar.close()
        
        # Merge all chunks
        print("\nMerging processed chunks...")
        result_doc = fitz.open()
        chunk_files = sorted(chunks_processed)
        
        merge_bar = tqdm(total=len(chunk_files), 
                        desc="Merging files",
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} files [{elapsed}<{remaining}]")
        
        for chunk_file in chunk_files:
            chunk_doc = fitz.open(chunk_file)
            result_doc.insert_pdf(chunk_doc)
            chunk_doc.close()
            os.remove(chunk_file)
            merge_bar.update(1)
        merge_bar.close()
        
        print(f"\nSaving final PDF to {output_path}")
        result_doc.save(output_path, garbage=4, deflate=True)
        result_doc.close()
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        # Clean up any remaining temporary files
        for f in os.listdir(output_dir):
            if f.startswith('temp_chunk_'):
                try:
                    os.remove(os.path.join(output_dir, f))
                except:
                    pass
        raise e

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_inverter.py <input_pdf_path> [output_pdf_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    process_in_chunks(input_path, output_path)