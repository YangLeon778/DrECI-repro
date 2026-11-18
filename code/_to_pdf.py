"""用 Windows COM 把 DOCX/PPTX 转 PDF。"""
import sys
from pathlib import Path
import pythoncom  # noqa

ROOT = Path(r"e:\Trae CN\projects\machine-WB\DrECI_repro")


def docx2pdf(src):
    from win32com.client import Dispatch
    word = Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(str(src))
    out = src.with_suffix(".pdf")
    # wdFormatPDF = 17
    doc.SaveAs(str(out), FileFormat=17)
    doc.Close(False)
    word.Quit()
    print("->", out.name)


def pptx2pdf(src):
    from win32com.client import Dispatch
    ppt = Dispatch("PowerPoint.Application")
    ppt.Visible = True
    prs = ppt.Presentations.Open(str(src), WithWindow=True)
    out = src.with_suffix(".pdf")
    # ppSaveAsPDF = 32
    prs.SaveAs(str(out), 32)
    prs.Close()
    ppt.Quit()
    print("->", out.name)


if __name__ == "__main__":
    import win32com.client  # noqa: F401
    for name in ["第八组_DrECI_复现报告.docx", "第八组_DrECI_汇报.pptx"]:
        p = ROOT / name
        if name.endswith(".docx"):
            docx2pdf(p)
        else:
            pptx2pdf(p)
