from starlette.middleware import body_limit
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import re

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.platypus import (
    Paragraph,
    Frame,
    Spacer,
    ListFlowable,
    ListItem,
)


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

LETTERHEAD_PATH = (
    BASE_DIR
    / "app"
    / "static"
    / "images"
    / "letterhead.png"
)

STORAGE_DIR = BASE_DIR / "storage" / "documents"

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# FONT REGISTRATION
# ---------------------------------------------------------

FONT_DIR = BASE_DIR / "app" / "static" / "fonts"

FONT_NAME = "TimesNewRoman"

try:

    pdfmetrics.registerFont(
        TTFont(
            "TimesNewRoman",
            str(FONT_DIR / "times.ttf")
        )
    )

    pdfmetrics.registerFont(
        TTFont(
            "TimesNewRoman-Bold",
            str(FONT_DIR / "timesbd.ttf")
        )
    )

    pdfmetrics.registerFont(
        TTFont(
            "TimesNewRoman-Italic",
            str(FONT_DIR / "timesi.ttf")
        )
    )

    pdfmetrics.registerFont(
        TTFont(
            "TimesNewRoman-BoldItalic",
            str(FONT_DIR / "timesbi.ttf")
        )
    )

    pdfmetrics.registerFontFamily(
        "TimesNewRoman",
        normal="TimesNewRoman",
        bold="TimesNewRoman-Bold",
        italic="TimesNewRoman-Italic",
        boldItalic="TimesNewRoman-BoldItalic",
    )

    print("[PDF Generator] Times New Roman font family registered successfully.")

except Exception as e:

    print(
        f"[PDF Generator] Custom font registration warning: "
        f"{e}. Falling back to standard Times-Roman."
    )

    FONT_NAME = "Times-Roman"


# ---------------------------------------------------------
# FONTS
# ---------------------------------------------------------

if FONT_NAME == "TimesNewRoman":

    BOLD_FONT = "TimesNewRoman-Bold"
    ITALIC_FONT = "TimesNewRoman-Italic"
    BOLD_ITALIC_FONT = "TimesNewRoman-BoldItalic"

else:

    BOLD_FONT = "Times-Bold"
    ITALIC_FONT = "Times-Italic"
    BOLD_ITALIC_FONT = "Times-BoldItalic"


# ---------------------------------------------------------
# LAYOUT
# ---------------------------------------------------------

PX_TO_PT = 0.75

FONT_SIZE = 12

LEFT_MARGIN = 70 * PX_TO_PT
RIGHT_MARGIN = 70 * PX_TO_PT

CONTENT_TOP = 165 * PX_TO_PT

CONTENT_WIDTH = A4[0] - LEFT_MARGIN - RIGHT_MARGIN


# ---------------------------------------------------------
# LIVE PREVIEW EQUIVALENTS
# ---------------------------------------------------------

BODY_LEADING = FONT_SIZE * 1.5

META_FONT_SIZE = 12

TOPIC_FONT_SIZE = 14

SUBJECT_FONT_SIZE = 12


# ---------------------------------------------------------
# HTML CLEANING
# ---------------------------------------------------------

def clean_rich_text(html: str) -> str:

    if not html:
        return ""

    html = html.replace("\r\n", "\n")
    html = html.replace("\r", "\n")

    # -----------------------------------------------------
    # Normalize bold
    # -----------------------------------------------------

    html = re.sub(
        r"<strong\b[^>]*>",
        "<b>",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</strong>",
        "</b>",
        html,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Normalize italic
    # -----------------------------------------------------

    html = re.sub(
        r"<em\b[^>]*>",
        "<i>",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</em>",
        "</i>",
        html,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Normalize line breaks
    # -----------------------------------------------------

    html = re.sub(
        r"<br\s*/?>",
        "<br/>",
        html,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Remove attributes from span
    #
    # IMPORTANT:
    # We are not yet preserving alignment styles here.
    # We'll handle that separately.
    # -----------------------------------------------------

    html = re.sub(
        r"<span\b[^>]*>",
        "<span>",
        html,
        flags=re.IGNORECASE
    )

    return html.strip()


# ---------------------------------------------------------
# BODY STYLE
# ---------------------------------------------------------

body_style = ParagraphStyle(
    "DocumentBody",

    fontName=FONT_NAME,

    fontSize=FONT_SIZE,

    leading=BODY_LEADING,

    alignment=TA_JUSTIFY,

    textColor=colors.black,

    spaceAfter=14 * PX_TO_PT,

    allowWidows=1,

    allowOrphans=1,

    # Tell ReportLab which fonts to use
    # when <b>, <i>, and <b><i> are encountered.
    boldFontName=BOLD_FONT,
    italicFontName=ITALIC_FONT,
    boldItalicFontName=BOLD_ITALIC_FONT,
)


# ---------------------------------------------------------
# TOPIC STYLE
# ---------------------------------------------------------

topic_style = ParagraphStyle(

    "DocumentTopic",

    fontName=BOLD_FONT,

    fontSize=TOPIC_FONT_SIZE,

    leading=TOPIC_FONT_SIZE * 1.3,

    alignment=TA_CENTER,

    textColor=colors.black,

    spaceBefore=0,

    spaceAfter=12,
)


# ---------------------------------------------------------
# SUBJECT STYLE
# ---------------------------------------------------------

subject_style = ParagraphStyle(

    "DocumentSubject",

    fontName=FONT_NAME,

    fontSize=SUBJECT_FONT_SIZE,

    leading=SUBJECT_FONT_SIZE * 1.45,

    alignment=TA_LEFT,

    textColor=colors.black,

    spaceAfter=20,
)


# ---------------------------------------------------------
# HTML → REPORTLAB
# ---------------------------------------------------------

def html_to_flowables(html: str):
    """
    Convert contenteditable HTML into ReportLab Paragraphs.

    Preserves:
        <b> / <strong>
        <i> / <em>
        <u>
        <br>
        <p>
        <ul>
        <ol>
        <li>
    """

    if not html:
        return []

    # Remove clipboard fragment markers
    html = re.sub(
        r"<!--\s*StartFragment\s*-->",
        "",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"<!--\s*EndFragment\s*-->",
        "",
        html,
        flags=re.IGNORECASE
    )

    # Normalize formatting tags
    html = re.sub(
        r"<strong\b[^>]*>",
        "<b>",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</strong\s*>",
        "</b>",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"<em\b[^>]*>",
        "<i>",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</em\s*>",
        "</i>",
        html,
        flags=re.IGNORECASE
    )

    # Normalize BR
    html = re.sub(
        r"<br\s*/?>",
        "<br/>",
        html,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Convert list items
    # -----------------------------------------------------

    html = re.sub(
        r"<li\b[^>]*>",
        "• ",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</li\s*>",
        "<br/>",
        html,
        flags=re.IGNORECASE
    )

    # Remove list containers
    html = re.sub(
        r"</?(ul|ol)\b[^>]*>",
        "",
        html,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Convert paragraph boundaries
    # -----------------------------------------------------

    html = re.sub(
        r"<p\b[^>]*>",
        "",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</p\s*>",
        "<br/><br/>",
        html,
        flags=re.IGNORECASE
    )

    # Remove div wrappers
    html = re.sub(
        r"<div\b[^>]*>",
        "",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r"</div\s*>",
        "<br/>",
        html,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Remove excessive breaks
    # -----------------------------------------------------

    html = re.sub(
        r"(?:<br/>\s*){3,}",
        "<br/><br/>",
        html,
        flags=re.IGNORECASE
    )

    html = html.strip()

    if not html:
        return []

    # -----------------------------------------------------
    # Split into logical paragraphs
    # -----------------------------------------------------

    parts = re.split(
        r"(?:<br/>\s*){2,}",
        html,
        flags=re.IGNORECASE
    )

    flowables = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        # Remove trailing single breaks
        part = re.sub(
            r"(?:<br/>\s*)+$",
            "",
            part,
            flags=re.IGNORECASE
        )

        if not part:
            continue

        flowables.append(
            Paragraph(
                part,
                body_style
            )
        )

    return flowables

# ---------------------------------------------------------
# PDF GENERATOR
# ---------------------------------------------------------

def generate_document_pdf(
    reference_no: str,
    student_name: str,
    enrollment_no: str,
    topic: str,
    subject: Optional[str],
    body: str,
    signature_authority: Optional[str] = None,
) -> Dict[str, Any]:


    print("\n========== PDF BODY HTML ==========")
    print(body)
    print("===================================\n")

    """
    Generate an official A4 PDF matching the live preview.

    Includes:

        Letterhead
        Reference number
        Date
        Topic heading
        Subject
        Rich-text body
        Justification
        Signature authority
    """

    year = datetime.now().year

    year_dir = (
        STORAGE_DIR
        / str(year)
    )

    year_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    safe_ref = (
        reference_no
        .replace("/", "-")
        .replace("\\", "-")
    )

    filename = (
        f"{safe_ref}.pdf"
    )

    pdf_path = (
        year_dir
        / filename
    )


    page_width, page_height = A4


    pdf = canvas.Canvas(
        str(pdf_path),
        pagesize=A4
    )


    # =====================================================
    # 1. LETTERHEAD
    # =====================================================

    if LETTERHEAD_PATH.exists():

        pdf.drawImage(
            str(LETTERHEAD_PATH),
            0,
            0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=False,
            mask="auto",
        )


    # =====================================================
    # 2. CONTENT POSITION
    # =====================================================

    content_left = LEFT_MARGIN

    content_right = (
        page_width
        - RIGHT_MARGIN
    )

    content_width = (
        content_right
        - content_left
    )


    # =====================================================
    # 3. REFERENCE + DATE
    # =====================================================

    # CSS:
    #
    # .document-content {
    #     top: 165px;
    # }
    #
    # .document-meta {
    #     margin-top: 70px;
    # }

    meta_top = (
        CONTENT_TOP
        + (70 * PX_TO_PT)
    )


    meta_baseline = (
        page_height
        - meta_top
        - (FONT_SIZE * 0.776 * 1.45)
    )


    today = datetime.now().strftime(
        "%d %B %Y"
    )


    pdf.setFont(
        FONT_NAME,
        META_FONT_SIZE
    )


    pdf.drawString(
        content_left,
        meta_baseline,
        f"Ref. No.: {reference_no}"
    )


    pdf.drawRightString(
        content_right,
        meta_baseline,
        today
    )


    # =====================================================
    # 4. TOPIC
    # =====================================================

    # This is the heading that appears between
    # Reference/Date and Subject in the live preview.

    topic = (
        topic or ""
    ).strip()


    topic_top = (
        meta_top
        + 35
    )


    if topic:

        topic_paragraph = Paragraph(
            escape(topic),
            topic_style
        )


        topic_width, topic_height = (
            topic_paragraph.wrap(
                content_width,
                100
            )
        )


        topic_paragraph.drawOn(
            pdf,
            content_left,
            page_height
            - topic_top
            - topic_height
        )


        current_top = (
            topic_top
            + topic_height
            + 8
        )

    else:

        current_top = (
            topic_top
        )


    # =====================================================
    # 5. SUBJECT
    # =====================================================

    if subject and subject.strip():

        subject_text = (
    "<b>Subject:</b> "
    + escape(subject.strip())
)


        subject_paragraph = Paragraph(
            subject_text,
            subject_style
        )


        subject_width, subject_height = (
            subject_paragraph.wrap(
                content_width,
                100
            )
        )


        subject_top = current_top


        subject_paragraph.drawOn(
            pdf,
            content_left,
            page_height
            - subject_top
            - subject_height
        )


        body_top = (
            subject_top
            + subject_height
            + 8
        )

    else:

        body_top = (
            current_top
            + 5
        )


    # =====================================================
    # 6. BODY
    # =====================================================

    flowables = html_to_flowables(
        body
    )


    body_bottom = 105


    available_body_height = (
        page_height
        - body_top
        - body_bottom
    )


    if flowables:

        frame = Frame(

            content_left,

            body_bottom,

            content_width,

            available_body_height,

            leftPadding=0,

            rightPadding=0,

            topPadding=0,

            bottomPadding=0,

            showBoundary=0,
        )


        frame.addFromList(
            flowables,
            pdf
        )


    # =====================================================
    # 7. SIGNATURE
    # =====================================================

    signature_text = (
        signature_authority
        or ""
    ).strip()


    signature_x = content_right


    signature_y = 98


    pdf.setFont(
        BOLD_FONT,
        FONT_SIZE
    )


    if signature_text:

        # Preserve multiple lines entered
        # in the signature authority field.

        lines = signature_text.split("\n")


        for index, line in enumerate(lines):

            pdf.drawRightString(
                signature_x,
                signature_y
                + (
                    (len(lines) - index - 1)
                    * (FONT_SIZE + 3)
                ),
                line.strip()
            )


    else:

        pdf.drawRightString(
            signature_x,
            signature_y,
            "Signing Authority"
        )


    # =====================================================
    # 8. SAVE
    # =====================================================

    pdf.save()


    return {

        "filename":
            filename,

        "path":
            str(pdf_path),

        "relative_url":
            f"/storage/documents/"
            f"{year}/{filename}"
    }


# ---------------------------------------------------------
# TEST WRAPPER
# ---------------------------------------------------------

def generate_test_pdf(
    reference_no: str,
    student_name: str,
    enrollment_no: str,
    topic: str,
    subject: Optional[str],
    body: str,
    signature_authority: Optional[str] = None,
) -> Dict[str, Any]:

    return generate_document_pdf(

        reference_no=reference_no,

        student_name=student_name,

        enrollment_no=enrollment_no,

        topic=topic,

        subject=subject,

        body=body,

        signature_authority=signature_authority,
    )