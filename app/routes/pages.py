from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.services.supabase_client import supabase


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =========================================================
# HOME / DOCUMENT GENERATOR
# =========================================================

@router.get("/")
def home(request: Request):

    response = (
        supabase
        .schema("bgiem_docs")
        .table("document_types")
        .select("code, name")
        .eq("is_active", True)
        .order("id")
        .execute()
    )

    current_date = datetime.now().strftime(
        "%d %B %Y"
    )

    return templates.TemplateResponse(
        request=request,
        name="document_form.html",
        context={
            "document_types": response.data,
            "current_date": current_date
        }
    )


# =========================================================
# LIST GENERATED DOCUMENTS
# =========================================================

@router.get("/documents")
def list_documents(request: Request):

    try:

        response = (
            supabase
            .schema("bgiem_docs")
            .table("documents")
            .select("*, document_types(code, name)")
            .order("created_at", desc=True)
            .execute()
        )

        documents = response.data or []

    except Exception as e:

        print(
            f"[Pages Router] Error querying documents list: {e}"
        )

        documents = []

    return templates.TemplateResponse(
        request=request,
        name="documents_list.html",
        context={
            "documents": documents
        }
    )

@router.get("/documents/new/{doc_code}")
def new_document(request: Request, doc_code: str):

    response = (
        supabase
        .schema("bgiem_docs")
        .table("document_types")
        .select("id, code, name")
        .eq("code", doc_code.upper())
        .single()
        .execute()
    )

    document_type = response.data or {}

    current_date = datetime.now().strftime("%d %B %Y")

    return templates.TemplateResponse(
        request=request,
        name="document_form.html",
        context={
            "document_type": document_type,
            "current_date": current_date
        }
    )