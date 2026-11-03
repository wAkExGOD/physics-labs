"""Check the generated report and render previews for visual inspection."""
from pathlib import Path
import sys

import pymupdf as fitz
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab5 import verify_sources


def main():
    verify_sources()
    document=fitz.open(ROOT/"lab5.pdf")
    assert "Панасика Владислава Александровича" in document[0].get_text()
    assert "Содержание" in document[1].get_text()
    assert len(document.get_toc())>=5
    log=(ROOT/"build/lab5.log").read_text(encoding="utf8")
    for error in ("Missing character:","Overfull ","There were undefined references","Label(s) may have changed","Float too large"):
        assert error not in log,error
    for path in (ROOT/"screenshots").glob("*.png"):
        Image.open(path).verify()
    sheet=Image.new("RGB",(3*310,((len(document)+2)//3)*450),"#dddddd")
    draw=ImageDraw.Draw(sheet)
    for i,page in enumerate(document):
        image=page.get_pixmap(matrix=fitz.Matrix(.5,.5),alpha=False)
        picture=Image.frombytes("RGB",[image.width,image.height],image.samples)
        picture.thumbnail((300,425))
        x=(i%3)*310+5
        y=(i//3)*450+20
        sheet.paste(picture,(x,y))
        draw.text((x,y-15),str(i+1),fill="black")
        if i in (0,1,4,6,8,9):
            page.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False).save(ROOT/"build"/f"page_{i+1}.png")
        print(f"Page {i+1}: {len(page.get_text())} text characters")
    sheet.save(ROOT/"build/report_preview.png")
    print(f"Checked {len(document)} pages, bookmarks, source hashes and screenshots.")


if __name__=="__main__":
    main()
