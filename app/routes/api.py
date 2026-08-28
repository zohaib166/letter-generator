from datetime import datetime
from pathlib import Path
from typing import Optional
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.supabase_client import supabase
from app.services.ai_service import generate_letter_content
from app.services.pdf_generator import generate_document_pdf, STORAGE_DIR, SIGNATURES_DIR


router = APIRouter(
    prefix="/api",
    tags=["Documents API"]
)


# ---------------------------------------------------------
# PYDANTIC MODELS
# ---------------------------------------------------------

class AIGenerateRequest(BaseModel):
    document_type_code: str
    student_name: str
    enrollment_no: str
    topic: str
    subject: Optional[str] = None
    word_limit: int = Field(default=250, ge=50, le=5000)
    # Simplified: Single field for additional information
    more_information: Optional[str] = None


class PDFGenerateRequest(BaseModel):
    document_type_id: Optional[int] = None
    document_type_code: str
    reference_no: Optional[str] = None
    enrollment_no: str
    student_name: str
    topic: str
    subject: Optional[str] = None
    receiver_address: Optional[str] = None
    body: str
    word_limit: int = 250
    signature_authority: Optional[str] = None
    signature_image: Optional[str] = None


# ---------------------------------------------------------
# REFERENCE NUMBER ROUTE
# ---------------------------------------------------------

@router.get("/reference-number/{document_type_code}")
def generate_reference_number(document_type_code: str):
    code = document_type_code.upper()

    try:
        response = (
            supabase
            .schema("bgiem_docs")
            .rpc("generate_reference_number", {"p_document_type_code": code})
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Reference number was not generated."
            )

        result = response.data[0]

        return {
            "status": "ok",
            "reference_number": result["reference_no"],
            "generated_year": result.get("generated_year"),
            "sequence": result.get("sequence_no")
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------------------------------------------------
# AI GENERATION ROUTE
# ---------------------------------------------------------

@router.post("/documents/generate-ai")
def api_generate_ai(payload: AIGenerateRequest):
    try:
        doc_type_res = (
            supabase
            .schema("bgiem_docs")
            .table("document_types")
            .select("name")
            .eq("code", payload.document_type_code.upper())
            .single()
            .execute()
        )

        document_type_name = doc_type_res.data["name"] if doc_type_res.data else "Official Letter"

        body = generate_letter_content(
            document_type_name=document_type_name,
            student_name=payload.student_name,
            enrollment_no=payload.enrollment_no,
            topic=payload.topic,
            subject=payload.subject,
            word_limit=payload.word_limit,
            # Simplified: Pass additional information as single field
            more_information=payload.more_information,
        )

        return {
            "status": "ok",
            "body": body,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )


# ---------------------------------------------------------
# PDF GENERATION ROUTE
# ---------------------------------------------------------

@router.post("/documents/generate-pdf")
def api_generate_pdf(payload: PDFGenerateRequest):
    try:
        code = payload.document_type_code.upper()

        # 1. Fetch document_type_id if missing
        doc_type_id = payload.document_type_id
        if not doc_type_id:
            dt_res = (
                supabase
                .schema("bgiem_docs")
                .table("document_types")
                .select("id")
                .eq("code", code)
                .single()
                .execute()
            )
            if dt_res.data:
                doc_type_id = dt_res.data["id"]
            else:
                doc_type_id = 1

        # 2. Generate or validate Reference Number
        ref_no = payload.reference_no
        sequence_no = None
        generated_year = datetime.now().year

        if not ref_no or "_" in ref_no or "TEST" in ref_no:

            rpc_res = (
                supabase
                .schema("bgiem_docs")
                .rpc(
                    "generate_reference_number",
                    {"p_document_type_code": code}
                )
                .execute()
            )

            if rpc_res.data:
                reference_data = rpc_res.data[0]

                ref_no = reference_data["reference_no"]
                sequence_no = reference_data["sequence_no"]
                generated_year = reference_data["generated_year"]

            else:
                raise HTTPException(
                    status_code=500,
                    detail="Reference number could not be generated."
                )

        else:
            # Existing/reference number supplied manually.
            # Extract sequence number from the final part of the reference number.
            try:
                sequence_no = int(ref_no.split("/")[-1])
            except (ValueError, IndexError):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid reference number format."
                )

        # 3. Generate PDF File via ReportLab Engine
        pdf_info = generate_document_pdf(
            reference_no=ref_no,
            student_name=payload.student_name,
            enrollment_no=payload.enrollment_no,
            topic=payload.topic,
            subject=payload.subject,
            receiver_address=payload.receiver_address,
            body=payload.body,
            signature_authority=payload.signature_authority,
            signature_image=payload.signature_image,
        )

        # 4. Insert Metadata Record into Supabase `bgiem_docs.documents`
        db_data = {
            "document_type_id": doc_type_id,
            "reference_no": ref_no,
            "sequence_no": sequence_no,
            "enrollment_no": payload.enrollment_no,
            "student_name": payload.student_name,
            "topic": payload.topic,
            "subject": payload.subject or "",
            "body": payload.body,
            "word_limit": payload.word_limit,
            "year": generated_year,
            "pdf_filename": pdf_info["filename"],
            "pdf_path": pdf_info["path"]
        }
        db_res = (
            supabase
            .schema("bgiem_docs")
            .table("documents")
            .insert(db_data)
            .execute()
        )

        doc_id = db_res.data[0]["id"] if db_res.data else None

        return {
            "status": "ok",
            "document_id": doc_id,
            "reference_no": ref_no,
            "filename": pdf_info["filename"],
            "download_url": f"/api/documents/download/{pdf_info['filename']}",
            "view_url": f"/storage/documents/{pdf_info['filename']}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF Generation failed: {str(e)}"
        )


# ---------------------------------------------------------
# PDF DOWNLOAD FILE ROUTE
# ---------------------------------------------------------

@router.get("/documents/download/{filename}")
def download_pdf(filename: str):
    # Search inside storage/documents directory recursively
    matched_files = list(STORAGE_DIR.rglob(filename))

    if not matched_files or not matched_files[0].exists():
        raise HTTPException(
            status_code=404,
            detail="Requested PDF file not found."
        )

    file_path = matched_files[0]

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )


# ---------------------------------------------------------
# SIGNATURE IMAGE ROUTES
# ---------------------------------------------------------

@router.get("/signatures")
def list_signatures():
    """
    Return a list of signature images saved in storage/signatures/.
    Each entry has { filename, url }.
    """
    SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}

    images = []

    for file in sorted(SIGNATURES_DIR.iterdir()):
        if file.is_file() and file.suffix.lower() in allowed_extensions:
            images.append({
                "filename": file.name,
                "url": f"/storage/signatures/{file.name}"
            })

    return {"status": "ok", "signatures": images}


@router.post("/signatures/upload")
async def upload_signature(file: UploadFile = File(...)):
    """
    Upload a signature image to storage/signatures/.
    Accepts PNG, JPEG, WEBP.
    """
    SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)

    allowed_content_types = {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
    }

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail="Only PNG, JPEG, and WebP images are allowed."
        )

    # Sanitise the filename
    safe_name = Path(file.filename).name

    dest_path = SIGNATURES_DIR / safe_name

    with dest_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    return {
        "status": "ok",
        "filename": safe_name,
        "url": f"/storage/signatures/{safe_name}"
    }


@router.get("/test-pdf")
def test_pdf():
    result = generate_document_pdf(
        reference_no="BGIEM/CSE/LOR/2026/999",
        student_name="Anushri Nema",
        enrollment_no="0246CS231050",
        topic="Application for Indian Army Internship Programme",
        subject="Recommendation for Internship",
        body=(
            "This is a test document generated by the BGIEM Document Generator. "
            "The purpose of this test is to verify A4 PDF generation, letterhead "
            "placement, typography, margins, and signing authority positioning."
        ),
    )

    return {
        "status": "ok",
        "file": result
    }