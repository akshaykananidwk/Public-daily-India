"""PDF પ્રેસ નોટ → ન્યુઝ. ડિઝાઈન કરેલી (ઈમેજ) PDF માટે Gemini Vision વાપરે.

દરેક પાનું ઈમેજમાં રેન્ડર થાય → Vision AI એને *જોઈને* સ્વચ્છ ગુજરાતી
ન્યુઝ કાઢે (કસ્ટમ ફોન્ટવાળી PDF માં ટેક્સ્ટ તૂટે એ સમસ્યા ટળે).
"""
import base64


def render_pages(pdf_path: str, dpi: int = 110, max_pages: int = 20):
    """PDF ના દરેક પાનાને JPEG bytes માં રેન્ડર કરે (નાનું). PyMuPDF જોઈએ."""
    import fitz
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pix = page.get_pixmap(dpi=dpi)
        try:
            pages.append(pix.tobytes("jpeg", jpg_quality=80))
        except Exception:
            pages.append(pix.tobytes("png"))
    doc.close()
    return pages


def extract_text(pdf_path: str) -> str:
    """સાદું ટેક્સ્ટ (સ્વચ્છ text-PDF માટે). ઈમેજ-PDF માં તૂટે."""
    import fitz
    doc = fitz.open(pdf_path)
    txt = "\n".join(p.get_text() for p in doc)
    doc.close()
    return txt


async def extract_news(pdf_path: str, llm, on_progress=None) -> tuple:
    """PDF માંથી (ન્યુઝ યાદી, પહેલી ભૂલ). Vision AI હોય તો દરેક પાનું જોઈને."""
    news, first_error = [], ""
    if llm.provider in ("gemini", "openai") and await llm.available():
        pages = render_pages(pdf_path)
        for i, img in enumerate(pages, 1):
            if on_progress:
                await on_progress(i, len(pages))
            b64 = base64.b64encode(img).decode()
            item = await llm.vision_news(b64)
            if item.get("error"):
                first_error = first_error or item["error"]
            elif item.get("title"):
                news.append(item)
        return news, first_error
    # Vision નથી — ટેક્સ્ટ ફોલબેક (ફકરા પ્રમાણે)
    text = extract_text(pdf_path)
    for para in text.split("\n\n"):
        para = para.strip()
        if len(para) > 60:
            news.append({"title": para.split("\n")[0][:120], "body": para})
    return news[:15], first_error
