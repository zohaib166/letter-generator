/* ==========================================
   ELEMENT REFERENCES
   ========================================== */

const docTypeCodeField = document.getElementById("document_type_code");
const enrollmentField = document.getElementById("enrollment_no");
const nameField = document.getElementById("student_name");
const topicField = document.getElementById("topic");
const subjectField = document.getElementById("subject");
const wordLimitField = document.getElementById("word_limit");
const bodyField = document.getElementById("body");
const signatureAuthorityField = document.getElementById("signature_authority");

const generateAiBtn = document.getElementById("generate-ai");
const aiStatus = document.getElementById("ai-status");
const generatePdfBtn = document.getElementById("generate-pdf");
const wordCount = document.getElementById("word-count");


/* ==========================================
   DOCUMENT HEADER ELEMENTS
   ========================================== */

const selectedDocumentCode =
    document.getElementById("selected-document-code");

const selectedDocumentName =
    document.getElementById("selected-document-name");


/* ==========================================
   PREVIEW ELEMENTS
   ========================================== */

const previewReference =
    document.getElementById("preview-reference");

const previewDate =
    document.getElementById("preview-date");

const previewTopic =
    document.getElementById("preview-topic");

const previewSubject =
    document.getElementById("preview-subject");

const previewSubjectContainer =
    document.getElementById("preview-subject-container");

const previewBody =
    document.getElementById("preview-body");

const previewSignature =
    document.getElementById("preview-signature");


/* ==========================================
   STATE
   ========================================== */

let currentReferenceNumber = "";


/* ==========================================
   DOCUMENT TYPE DEFAULTS
   ========================================== */

const documentDefaults = {

    LOR: {
        topic: "Letter of Recommendation",
        subject: "",
        wordLimit: 300
    },

    BON: {
        topic: "Bonafide Certificate",
        subject: "Bonafide Certificate",
        wordLimit: 200
    },

    NOC: {
        topic: "No Objection Certificate",
        subject: "No Objection Certificate",
        wordLimit: 250
    },

    RANK: {
        topic: "Rank Certificate",
        subject: "Rank Certificate",
        wordLimit: 200
    },

    APPT: {
        topic: "Appointment Letter",
        subject: "Appointment Letter",
        wordLimit: 300
    },

    INV: {
        topic: "Invitation Letter",
        subject: "Invitation",
        wordLimit: 300
    },

    CONS: {
        topic: "Consent Letter",
        subject: "Consent",
        wordLimit: 250
    },

    APP: {
        topic: "Appreciation Letter",
        subject: "Appreciation",
        wordLimit: 250
    },

    DUTY: {
        topic: "Duty Certificate",
        subject: "Duty Certificate",
        wordLimit: 200
    },

    OTH: {
        topic: "",
        subject: "",
        wordLimit: 250
    }
};


/* ==========================================
   DOCUMENT TYPE CHANGE
   ========================================== */

function handleDocumentTypeChange() {

    if (!docTypeCodeField) {
        return;
    }

    const selectedOption =
        docTypeCodeField.options[
        docTypeCodeField.selectedIndex
        ];

    if (!selectedOption || !selectedOption.value) {

        if (selectedDocumentCode) {
            selectedDocumentCode.textContent = "BGIEM";
        }

        if (selectedDocumentName) {
            selectedDocumentName.textContent =
                "Create Official Document";
        }

        if (topicField) {
            topicField.value = "";
        }

        if (subjectField) {
            subjectField.value = "";
        }

        if (wordLimitField) {
            wordLimitField.value = 250;
        }

        currentReferenceNumber = "";

        if (previewReference) {
            previewReference.textContent =
                "Ref. No.: Will be assigned on generation";
        }

        updateWordCount();
        updateTopicPreview();
        updateSubjectPreview();

        return;
    }

    const code = selectedOption.value;

    const name =
        selectedOption.dataset.name || code;


    /* Update heading */

    if (selectedDocumentCode) {
        selectedDocumentCode.textContent = code;
    }

    if (selectedDocumentName) {
        selectedDocumentName.textContent = name;
    }


    /* Apply defaults */

    const defaults =
        documentDefaults[code];

    if (defaults) {

        if (topicField) {
            topicField.value =
                defaults.topic || "";
        }

        if (subjectField) {
            subjectField.value =
                defaults.subject || "";
        }

        if (wordLimitField) {
            wordLimitField.value =
                defaults.wordLimit || 250;
        }
    }


    /* Reset reference number */

    currentReferenceNumber = "";

    if (previewReference) {

        previewReference.textContent =
            "Ref. No.: Will be assigned on generation";
    }


    updateWordCount();
    updateTopicPreview();
    updateSubjectPreview();
}


/* ==========================================
   WORD COUNT
   ========================================== */

function countWords(text) {

    return text
        .trim()
        .split(/\s+/)
        .filter(w => w.length > 0)
        .length;
}


function updateWordCount() {

    if (!bodyField || !wordLimitField || !wordCount) {
        return;
    }

    const text =
        bodyField.innerText || "";

    const count =
        countWords(text);

    const limit =
        parseInt(wordLimitField.value) || 0;


    if (limit > 0) {

        wordCount.textContent =
            `${count} / ${limit} words`;

        wordCount.style.color =
            count > limit
                ? "#dc2626"
                : "#6b7280";

    } else {

        wordCount.textContent =
            `${count} words`;
    }
}


/* ==========================================
   BODY PREVIEW
   ========================================== */

function updateBodyPreview() {

    if (!bodyField || !previewBody) {
        return;
    }

    const html =
        bodyField.innerHTML.trim();


    if (!html) {

        previewBody.innerHTML =
            "<p>The letter body will appear here...</p>";

        return;
    }


    previewBody.innerHTML =
        sanitizeRichText(html);
}

function sanitizeRichText(html) {

    const template =
        document.createElement("template");

    template.innerHTML = html;


    const allowedTags = [
        "P",
        "BR",
        "STRONG",
        "B",
        "EM",
        "I",
        "U",
        "UL",
        "OL",
        "LI",
        "DIV",
        "SPAN"
    ];


    template.content
        .querySelectorAll("*")
        .forEach(element => {

            if (!allowedTags.includes(element.tagName)) {

                element.replaceWith(
                    document.createTextNode(
                        element.textContent
                    )
                );

                return;
            }


            /*
             * Remove potentially unsafe attributes.
             * We don't need arbitrary pasted HTML
             * attributes in our official document.
             */

            [...element.attributes]
                .forEach(attribute => {

                    element.removeAttribute(
                        attribute.name
                    );

                });

        });


    return template.innerHTML;
}

/* ==========================================
   SUBJECT PREVIEW
   ========================================== */

function updateSubjectPreview() {

    if (!subjectField ||
        !previewSubjectContainer ||
        !previewSubject) {

        return;
    }


    const subject =
        subjectField.value.trim();


    if (!subject) {

        previewSubjectContainer.style.display =
            "none";

        return;
    }


    previewSubjectContainer.style.display =
        "block";

    previewSubject.textContent =
        subject;
}


/* ==========================================
   TOPIC PREVIEW
   ========================================== */

/* ==========================================
   TOPIC / PURPOSE PREVIEW
   ========================================== */

function updateTopicPreview() {

    if (!topicField || !previewTopic) {
        return;
    }

    const topic = topicField.value.trim();

    if (!topic) {
        previewTopic.style.display = "none";
        previewTopic.textContent = "";
        return;
    }

    previewTopic.style.display = "block";
    previewTopic.textContent = topic;
}

/* ==========================================
   SIGNATURE AUTHORITY PREVIEW
   ========================================== */

function updateSignaturePreview() {

    if (!signatureAuthorityField ||
        !previewSignature) {

        return;
    }


    const authority =
        signatureAuthorityField.value.trim();


    if (!authority) {

        previewSignature.innerHTML =
            "__________________________";

        return;
    }


    /*
       Preserve multiple lines entered
       by the user.
    */

    const lines =
        authority
            .split("\n")
            .map(line => escapeHtml(line.trim()))
            .filter(line => line.length > 0);


    previewSignature.innerHTML =
        lines.join("<br>");
}


/* ==========================================
   HTML ESCAPE
   ========================================== */

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


/* ==========================================
   AI GENERATION
   ========================================== */

async function handleGenerateAI() {

    const studentName =
        nameField ? nameField.value.trim() : "";

    const topic =
        topicField ? topicField.value.trim() : "";

    const enrollmentNo =
        enrollmentField ? enrollmentField.value.trim() : "";

    const subject =
        subjectField ? subjectField.value.trim() : "";

    const wordLimit =
        wordLimitField
            ? parseInt(wordLimitField.value) || 250
            : 250;

    const docCode =
        docTypeCodeField
            ? docTypeCodeField.value
            : "";


    if (!docCode) {

        alert(
            "Please select a document type first."
        );

        if (docTypeCodeField) {
            docTypeCodeField.focus();
        }

        return;
    }


    if (!studentName || !topic) {

        alert(
            "Please enter both Student Name and Topic / Purpose before generating with AI."
        );

        if (!studentName && nameField) {
            nameField.focus();
        } else if (topicField) {
            topicField.focus();
        }

        return;
    }


    generateAiBtn.disabled = true;
    generateAiBtn.style.opacity = "0.7";

    aiStatus.textContent =
        "✨ Draft with AI...";


    try {

        const response =
            await fetch(
                "/api/documents/generate-ai",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        document_type_code:
                            docCode,

                        student_name:
                            studentName,

                        enrollment_no:
                            enrollmentNo || "N/A",

                        topic:
                            topic,

                        subject:
                            subject,

                        word_limit:
                            wordLimit
                    })
                }
            );


        const data =
            await response.json();


        if (response.ok && data.body) {

            bodyField.innerHTML =
                sanitizeRichText(
                    data.body
                );

            updateWordCount();
            updateBodyPreview();

            aiStatus.textContent =
                "✅ Generated successfully!";

        } else {

            aiStatus.textContent =
                `❌ ${data.detail ||
                "AI generation failed."
                }`;
        }


    } catch (err) {

        console.error(
            "AI Generation error:",
            err
        );

        aiStatus.textContent =
            "❌ Network error generating letter.";

    } finally {

        generateAiBtn.disabled = false;
        generateAiBtn.style.opacity = "1";

        setTimeout(() => {

            if (
                aiStatus.textContent.includes("✅")
            ) {
                aiStatus.textContent = "";
            }

        }, 3000);
    }
}


/* ==========================================
   PDF GENERATION
   ========================================== */

async function handleGeneratePDF() {

    const enrollmentNo =
        enrollmentField.value.trim();

    const studentName =
        nameField.value.trim();

    const topic =
        topicField.value.trim();

    const subject =
        subjectField.value.trim();

    const body =
        bodyField.innerHTML.trim();

    const signatureAuthority =
        signatureAuthorityField
            ? signatureAuthorityField.value.trim()
            : "";

    const wordLimit =
        parseInt(wordLimitField.value) || 250;

    const docCode =
        docTypeCodeField
            ? docTypeCodeField.value
            : "";


    /* ======================================
       VALIDATION
       ====================================== */

    if (!docCode) {

        alert(
            "Please select a document type."
        );

        docTypeCodeField.focus();

        return;
    }


    if (!enrollmentNo) {

        alert(
            "Enrollment Number is required."
        );

        enrollmentField.focus();

        return;
    }


    if (!studentName) {

        alert(
            "Student Name is required."
        );

        nameField.focus();

        return;
    }


    if (!topic) {

        alert(
            "Topic / Purpose is required."
        );

        topicField.focus();

        return;
    }


    if (!body) {

        alert(
            "Letter Body is empty. Please enter or generate the body content."
        );

        bodyField.focus();

        return;
    }


    /* ======================================
       GENERATE
       ====================================== */

    generatePdfBtn.disabled =
        true;

    generatePdfBtn.textContent =
        "⏳ Generating PDF...";


    try {

        const response =
            await fetch(
                "/api/documents/generate-pdf",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        document_type_code:
                            docCode,

                        /*
                           IMPORTANT:
                           We intentionally don't
                           send a reference number.

                           The server will generate
                           the next sequential number
                           only when the PDF is created.
                        */

                        reference_no:
                            "",

                        enrollment_no:
                            enrollmentNo,

                        student_name:
                            studentName,

                        topic:
                            topic,

                        subject:
                            subject,

                        body:
                            body,

                        word_limit:
                            wordLimit,

                        signature_authority:
                            signatureAuthority
                    })
                }
            );


        const data =
            await response.json();


        if (
            response.ok &&
            data.download_url
        ) {

            currentReferenceNumber =
                data.reference_no;


            if (previewReference) {

                previewReference.textContent =
                    `Ref. No.: ${data.reference_no}`;
            }


            window.open(
                data.download_url,
                "_blank"
            );


            alert(
                `Document generated successfully!\nReference: ${data.reference_no}`
            );


        } else {

            alert(
                `Failed to generate PDF: ${data.detail ||
                "Unknown error"
                }`
            );
        }


    } catch (err) {

        console.error(
            "PDF generation error:",
            err
        );

        alert(
            "Network error while generating PDF."
        );


    } finally {

        generatePdfBtn.disabled =
            false;

        generatePdfBtn.textContent =
            "Generate PDF";
    }
}


/* ==========================================
   EVENT LISTENERS
   ========================================== */

if (docTypeCodeField) {

    docTypeCodeField.addEventListener(
        "change",
        handleDocumentTypeChange
    );
}


if (bodyField) {

    bodyField.addEventListener(
        "input",
        () => {

            updateWordCount();
            updateBodyPreview();

        }
    );
}

/* ==========================================
   RICH TEXT PASTE
   ========================================== */

if (bodyField) {

    bodyField.addEventListener(
        "paste",
        event => {

            event.preventDefault();

            const clipboard =
                event.clipboardData;

            if (!clipboard) {
                return;
            }

            const html =
                clipboard.getData("text/html");

            const text =
                clipboard.getData("text/plain");


            if (html) {

                bodyField.focus();

                const cleanHtml =
                    sanitizeRichText(html);

                document.execCommand(
                    "insertHTML",
                    false,
                    cleanHtml
                );

            } else {

                document.execCommand(
                    "insertText",
                    false,
                    text
                );

            }

            updateWordCount();
            updateBodyPreview();

        }
    );

}

/* ==========================================
   RICH TEXT TOOLBAR
   ========================================== */

const richTextToolbar =
    document.querySelector(".rich-text-toolbar");


if (richTextToolbar && bodyField) {

    richTextToolbar
        .querySelectorAll("button[data-command]")
        .forEach(button => {

            button.addEventListener(
                "mousedown",
                event => {

                    /*
                     * Prevent losing the current
                     * text selection.
                     */

                    event.preventDefault();
                }
            );


            button.addEventListener(
                "click",
                () => {

                    const command =
                        button.dataset.command;

                    bodyField.focus();

                    document.execCommand(
                        command,
                        false,
                        null
                    );

                    updateWordCount();
                    updateBodyPreview();

                }
            );

        });

}


if (wordLimitField) {

    wordLimitField.addEventListener(
        "input",
        updateWordCount
    );
}


if (subjectField) {

    subjectField.addEventListener(
        "input",
        updateSubjectPreview
    );
}

if (topicField) {

    topicField.addEventListener(
        "input",
        updateTopicPreview
    );
}


if (signatureAuthorityField) {

    signatureAuthorityField.addEventListener(
        "input",
        updateSignaturePreview
    );
}


if (generateAiBtn) {

    generateAiBtn.addEventListener(
        "click",
        handleGenerateAI
    );
}


if (generatePdfBtn) {

    generatePdfBtn.addEventListener(
        "click",
        handleGeneratePDF
    );
}


/* ==========================================
   INITIALIZE
   ========================================== */

updateWordCount();

updateBodyPreview();

updateTopicPreview();

updateSubjectPreview();

updateSignaturePreview();

if (previewDate) {

    const now =
        new Date();

    previewDate.textContent =
        now.toLocaleDateString(
            "en-GB",
            {
                day: "2-digit",
                month: "long",
                year: "numeric"
            }
        );
}