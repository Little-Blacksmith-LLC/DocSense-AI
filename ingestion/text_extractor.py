#!/usr/bin/env python3
"""
DocSense AI - Text Extractor (Fixed folder creation + Drive links)
"""

import json
from pathlib import Path
import pymupdf4llm
import fitz  # PyMuPDF core
import os

# Import config
from ingestion.config import (
    DOWNLOAD_FOLDER, 
    EXTRACTED_FOLDER, 
    IMAGES_BASE, 
    METADATA_FILE
)

MIN_IMAGE_WIDTH = 80
MIN_IMAGE_HEIGHT = 80

def extract_text_structure(pdf_path: Path) -> dict:
    print(f"📄 Extracting text & structure: {pdf_path.name}")
    try:
        pages_data = pymupdf4llm.to_markdown(
            str(pdf_path),
            page_chunks=True,
            write_images=False,
            table_strategy="lines_strict",
            force_text=True,
        )
        full_markdown = "\n\n".join(p.get("text", "") for p in pages_data)
       
        all_tables = []
        for page in pages_data:
            page_num = page.get("metadata", {}).get("page", 0)
            if page.get("tables"):
                for idx, t in enumerate(page["tables"]):
                    all_tables.append({
                        "page_number": page_num,
                        "table_index": idx,
                        "markdown": t.get("markdown") or t.get("text", "")
                    })
        return {
            "document_name": pdf_path.name,
            "full_markdown": full_markdown,
            "pages": pages_data,
            "tables": all_tables,
            "total_pages": len(pages_data),
        }
    except Exception as e:
        print(f"⚠️ Text fallback: {e}")
        md_text = pymupdf4llm.to_markdown(str(pdf_path))
        return {"document_name": pdf_path.name, "full_markdown": md_text}

def extract_images_reliably(pdf_path: Path, doc_image_dir: Path) -> list:
    """Extract only meaningful-sized images (skip tiny checkboxes/dots)."""
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    w, h = pix.width, pix.height
                   
                    if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
                        print(f" ⏭️ Skipped tiny image on page {page_num+1}: {w}x{h}")
                        pix = None
                        continue
                   
                    img_filename = f"page{page_num+1}_img{img_idx+1}.png"
                    img_path = doc_image_dir / img_filename
                    pix.save(str(img_path))
                   
                    images.append({
                        "page_number": page_num + 1,
                        "image_index": img_idx + 1,
                        "file_path": str(img_path.relative_to(IMAGES_BASE.parent)),
                        "width": w,
                        "height": h,
                    })
                    print(f" 📸 Kept image on page {page_num+1}: {w}x{h}")
                    pix = None
                except Exception:
                    continue
        doc.close()
    except Exception as e:
        print(f" ⚠️ Image extraction issue: {e}")
    return images

def add_image_placeholders(markdown: str, images: list) -> str:
    if not images:
        return markdown
    placeholder = "\n\n## 📸 Extracted Images\n\n"
    for img in images:
        placeholder += f"**Page {img['page_number']}** — {img['width']}×{img['height']} px \n"
        placeholder += f"![Image]({img['file_path']})\n\n"
    return markdown + placeholder

def process_pdf(pdf_path: Path, relative_folder: str):
    try:
        data = extract_text_structure(pdf_path)
       
        # === Attach Google Drive link ===
        rel_path = str(pdf_path.relative_to(DOWNLOAD_FOLDER))
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                drive_meta = json.load(f)
            file_meta = drive_meta.get(rel_path, {})
            data["drive_file_id"] = file_meta.get("file_id")
            data["drive_web_view_link"] = file_meta.get("web_view_link")
            data["drive_link"] = (file_meta.get("web_view_link") or 
                                  f"https://drive.google.com/file/d/{file_meta.get('file_id')}/view")
        except Exception as e:
            print(f" ⚠️ Could not load Drive metadata for {pdf_path.name}: {e}")
            data["drive_file_id"] = None
            data["drive_web_view_link"] = None
            data["drive_link"] = None

        # Create image directory
        doc_image_dir = IMAGES_BASE / pdf_path.stem
        doc_image_dir.mkdir(parents=True, exist_ok=True)
        data["images"] = extract_images_reliably(pdf_path, doc_image_dir)
       
        data["full_markdown"] = add_image_placeholders(data["full_markdown"], data["images"])
       
        data.update({
            "source_path": str(pdf_path),
            "relative_folder": relative_folder,
            "file_size_bytes": pdf_path.stat().st_size,
        })
       
        # Ensure output folder exists
        EXTRACTED_FOLDER.mkdir(parents=True, exist_ok=True)
       
        output_json = EXTRACTED_FOLDER / f"{pdf_path.stem}.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
       
        md_path = EXTRACTED_FOLDER / f"{pdf_path.stem}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_path.name}\n\n**Folder:** {relative_folder}\n\n")
            f.write(data["full_markdown"])
       
        print(f"✅ Done → {output_json.name} | 📸 {len(data.get('images', []))} images | 🔗 Drive link attached")

    except Exception as e:
        print(f"❌ Failed {pdf_path.name}: {e}")

def main():
    print("🚀 Starting extraction with smart image filtering + Drive links...")
    print("=" * 90)
   
    # Ensure output folders exist before processing
    EXTRACTED_FOLDER.mkdir(parents=True, exist_ok=True)
    IMAGES_BASE.mkdir(parents=True, exist_ok=True)
   
    pdf_count = 0
    for root, _, files in os.walk(DOWNLOAD_FOLDER):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = Path(root) / file
                rel_path = pdf_path.relative_to(DOWNLOAD_FOLDER)
                relative_folder = str(rel_path.parent) if str(rel_path.parent) != "." else "."
                process_pdf(pdf_path, relative_folder.replace("\\", "/"))
                pdf_count += 1
   
    print(f"\n🎉 Extraction completed! Processed {pdf_count} PDFs.")
    print(f" → Markdown + JSON: {EXTRACTED_FOLDER}/")
    print(f" → Clean images: {IMAGES_BASE}/")

if __name__ == "__main__":
    main()
