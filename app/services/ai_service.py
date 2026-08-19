import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def generate_letter_content(
    document_type_name: str,
    student_name: str,
    enrollment_no: str,
    topic: str,
    subject: Optional[str] = None,
    word_limit: int = 250,
    more_information: Optional[str] = None,
) -> str:
    """
    Generate formal institutional letter body content using Gemini AI
    with an intelligent template fallback if API key is unconfigured or fails.
    """
    # Checks for GEMINI_API_KEY first, with GOOGLE_API_KEY as secondary fallback
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            prompt = (
                f"You are writing an official document for Baderia Global Institute of Engineering and Management, Jabalpur (BGIEM).\n"
                f"Document Type: {document_type_name}\n"
                f"Student Name: {student_name}\n"
                f"Enrollment Number: {enrollment_no}\n"
                f"Topic / Purpose: {topic}\n"
                f"Subject: {subject or 'Official Document'}\n"
                f"Target Word Limit: ~{word_limit} words.\n"
                f"Additional Information: {more_information or 'None'}\n\n"
                f"Instructions:\n"
                f"1. Write ONLY the formal body of the letter/certificate (do not include date, header, reference number, or signature line as those are generated separately).\n"
                f"2. Use formal academic/institutional English suitable for a top educational institute.\n"
                f"3. Organize into clear, well-structured paragraphs (separated by blank lines).\n"
                f"4. Directly address the topic and highlight the student's credentials, good conduct, and performance.\n"
                f"5. Keep the total length around {word_limit} words.\n"
                f"6. Use the institution name exactly as provided.\n"
                f"7. Do not use Bansal Group of Institutes or any other institution name.\n"
                f"8. Do not invent departments, addresses, affiliations, authorities, or institutional details.\n"
                f"9. Incorporate the additional information provided in the 'More Information' field to enhance the letter content."
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            if response and response.text:
                return response.text.strip()

        except Exception as e:
            print(f"[AI Service] Gemini API call failed: {e}. Falling back to template generator.")
            # Explicitly return fallback content on exception so the backend never sends None
            return _generate_fallback_letter(
                document_type_name=document_type_name,
                student_name=student_name,
                enrollment_no=enrollment_no,
                topic=topic,
                subject=subject,
                word_limit=word_limit,
                more_information=more_information,
            )

    # Fallback Generator (Runs if API key is not configured in .env)
    return _generate_fallback_letter(
        document_type_name=document_type_name,
        student_name=student_name,
        enrollment_no=enrollment_no,
        topic=topic,
        subject=subject,
        word_limit=word_limit,
        more_information=more_information,
    )


def _generate_fallback_letter(
    document_type_name: str,
    student_name: str,
    enrollment_no: str,
    topic: str,
    subject: Optional[str],
    word_limit: int,
    more_information: Optional[str] = None,
) -> str:
    """
    Generates a high-quality, formal institutional document body.
    """
    subject_text = f" regarding '{subject}'" if subject else ""
    more_info_text = f" Additional Information: {more_information}" if more_information else ""

    paragraph_1 = (
        f"This is to certify that {student_name} (Enrollment No.: {enrollment_no}) is a bonafide student "
        f"of Baderia Global Institute of Engineering and Management, Jabalpur (BGIEM). This official {document_type_name} is being issued "
        f"in connection with {topic}{subject_text}.{more_info_text}"
    )

    paragraph_2 = (
        f"During the tenure at our institution, {student_name} has demonstrated exemplary academic performance, "
        f"strong ethical discipline, and active involvement in technical and extracurricular endeavors. "
        f"{student_name} possesses impressive analytical capabilities, diligence, and a commendable work ethic "
        f"that reflects the core values of BGIEM."
    )

    paragraph_3 = (
        f"We strongly endorse {student_name} for this opportunity and extend our best wishes for all future "
        f"academic and professional pursuits. Please feel free to contact the institution administration "
        f"should any further verification be required."
    )

    return f"{paragraph_1}\n\n{paragraph_2}\n\n{paragraph_3}"