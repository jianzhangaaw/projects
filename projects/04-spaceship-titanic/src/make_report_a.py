"""生成《机器学习实践》大作业报告：markdown → docx → PDF，并做产物校验。"""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "out"
DOCX = LAB / "【机器学习实践】大作业报告.docx"
PDF = LAB / "【机器学习实践】大作业报告.pdf"

sys.path.insert(0, str(LAB / "src"))
import build_report_a  # noqa: E402
from md2docx import md_to_docx, new_doc, para  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402

# LibreOffice：按常见的安装位置查找，找不到就报错提示（本机为 C:\Program Files\LibreOffice）
def _find_soffice() -> str:
    import shutil
    for cand in [r"C:\Program Files\LibreOffice\program\soffice.com",
                 r"C:\Program Files (x86)\LibreOffice\program\soffice.com"]:
        if Path(cand).exists():
            return cand
    found = shutil.which("soffice") or shutil.which("soffice.com")
    if found:
        return found
    raise FileNotFoundError(
        "未找到 LibreOffice。请安装后重试，或手动用 Word 打开生成的 docx 另存为 PDF。\n"
        "说明：本脚本用 LibreOffice 把 docx 转成 PDF，这一步不是实验本身必需的。")


LO = _find_soffice()
# profile 目录放在实验目录下的 tmp/，避免依赖固定的本机路径
PROFILE_DIR = LAB / "tmp" / "lo-profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
PROFILE = PROFILE_DIR.as_uri()


def main():
    res = build_report_a.load()
    body, _ = build_report_a.build(res)
    (OUT / "report_a_body.md").write_text(body, encoding="utf-8")
    print(f"正文 markdown：{len(body)} 字符")

    doc = new_doc()
    para(doc, "《机器学习实践》课程大作业报告", size=16, bold=True, indent=0,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
    doc = md_to_docx(body, doc=doc, img_base=OUT)
    # 去掉标题行（md 里的一级标题已在正文中作为首行出现）
    doc.save(DOCX)
    print(f"写出 {DOCX}  {DOCX.stat().st_size} 字节  段落 {len(doc.paragraphs)}")

    r = subprocess.run([LO, f"-env:UserInstallation={PROFILE}", "--headless",
                        "--convert-to", "pdf", "--outdir", str(LAB), str(DOCX)],
                       capture_output=True, text=True, timeout=600)
    print("LibreOffice 返回码:", r.returncode)
    if not PDF.exists():
        print("PDF 未生成，stdout/stderr：", r.stdout[-800:], r.stderr[-800:])
        sys.exit(1)
    print(f"写出 {PDF}  {PDF.stat().st_size} 字节")


if __name__ == "__main__":
    main()
