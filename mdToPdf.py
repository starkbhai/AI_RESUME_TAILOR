import markdown
from xhtml2pdf import pisa
from pathlib import Path

# CSS Styling
RESUME_CSS = """
@page {
    margin: 15mm 18mm;
    size: A4;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #1a1a1a;
}

h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #111111;
    margin-bottom: 2px;
    margin-top: 0;
}

h2 {
    font-size: 11pt;
    font-weight: bold;
    color: #1d4ed8;
    border-bottom: 1px solid #1d4ed8;
    padding-bottom: 2px;
    margin-top: 12px;
    margin-bottom: 5px;
    text-transform: uppercase;
}

h3 {
    font-size: 10pt;
    font-weight: bold;
    color: #111111;
    margin-top: 6px;
    margin-bottom: 2px;
}

p {
    font-size: 10pt;
    margin-bottom: 4px;
    margin-top: 0;
}

ul {
    margin-left: 15px;
    margin-bottom: 4px;
    margin-top: 2px;
}

li {
    font-size: 10pt;
    margin-bottom: 2px;
}

hr {
    border-top: 1px solid #e5e7eb;
    margin: 6px 0;
}

a {
    color: #1d4ed8;
    text-decoration: none;
}

strong {
    font-weight: bold;
}
"""


def md_to_pdf(markdown_file: str, output_pdf: str):
    """
    Convert Markdown file to PDF
    """

    # Read markdown file
    with open(markdown_file, "r", encoding="utf-8") as file:
        md_text = file.read()

    # Convert Markdown -> HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["extra", "sane_lists"]
    )

    # Full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {RESUME_CSS}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    # Create output directory if it doesn't exist
    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)

    # Generate PDF
    with open(output_pdf, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(
            full_html,
            dest=pdf_file
        )

    # Status
    if pisa_status.err:
        print("❌ PDF generation failed")
    else:
        print(f"✅ PDF generated successfully: {output_pdf}")


if __name__ == "__main__":

    markdown_file = "./output/resume_tailored_20260517_121834.md"

    output_pdf = "./output/resume_tailored_20260517_121834_new.pdf"

    md_to_pdf(markdown_file, output_pdf)