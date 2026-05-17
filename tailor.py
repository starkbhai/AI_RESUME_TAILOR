#!/usr/bin/env python3
"""
Resume Tailor — ATS-optimized resume generator
Usage: python tailor.py --resume input/base_resume.md --jd input/job_description.txt
"""

import argparse
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# import anthropic
import markdown
from xhtml2pdf import pisa
from openai import OpenAI
from config import Config




# ── Prompt (lean: max signal, min tokens) ────────────────────────────────────

SYSTEM_PROMPT = """You are an expert ATS resume writer. Rewrite the given resume to match the job description.

Rules:
- Mirror keywords/phrases from JD exactly (ATS parsing)
- Keep ALL facts true — never invent experience or skills
- Strengthen weak bullet points with action verbs + impact
- Add a tight 2-line Summary aligned to the role
- Order Skills to front-load JD keywords
- Remove irrelevant content
- Output ONLY the final Markdown resume — no explanation, no fences"""

USER_TEMPLATE = """JD:
{jd}

RESUME:
{resume}

Output the ATS-tailored Markdown resume."""


# ── PDF CSS (clean, ATS-printable, single-column) ────────────────────────────


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
    font-size: 9.5pt;
    font-weight: bold;
    color: #1d4ed8;
    border-bottom: 1px solid #1d4ed8;
    padding-bottom: 1px;
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
    margin-bottom: 1px;
}
 
hr {
    border-top: 1px solid #e5e7eb;
    margin: 6px 0;
}
 
a { color: #1d4ed8; }
strong { font-weight: bold; }
"""


# ── Core functions ─────────────────────────────────────────────────────────────

def tailor_with_ai(resume_md: str, jd: str) -> str:
    """Call Claude API with minimal tokens, return tailored Markdown."""
    # client = anthropic.Anthropic()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key= Config.OPENAI_API_KEY,  # <-- Replace with your actual key
    )

    # Trim whitespace to reduce tokens
    resume_md = re.sub(r'\n{3,}', '\n\n', resume_md.strip())
    jd = re.sub(r'\n{3,}', '\n\n', jd.strip())

    completion = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": USER_TEMPLATE.format(
                    jd=jd,
                    resume=resume_md
                )
            }
        ]
    )



    # message = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=1800,          # enough for 1-page resume
    #     system=SYSTEM_PROMPT,
    #     messages=[{
    #         "role": "user",
    #         "content": USER_TEMPLATE.format(jd=jd, resume=resume_md)
    #     }]
    # )

    result = completion.choices[0].message.content

    # Strip accidental code fences
    result = re.sub(r'^```(?:markdown)?\s*', '', result)
    result = re.sub(r'\s*```$', '', result)

    # Token usage report
    usage = completion.usage
    print(f"  Tokens → input: {usage.prompt_tokens} | output: {usage.completion_tokens} "
          f"| total: {usage.total_tokens}")

    return result


def md_to_pdf(md_text: str, output_path: str) -> None:
    """Markdown -> HTML -> PDF via xhtml2pdf (pure Python, Windows safe)."""
    html_body = markdown.markdown(md_text, extensions=["extra", "sane_lists"])
 
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Resume</title>
    <style>{RESUME_CSS}</style>
</head>
<body>{html_body}</body>
</html>"""
 
    with open(output_path, "wb") as pdf_file:
        result = pisa.CreatePDF(full_html, dest=pdf_file)
 
    if result.err:
        print(f"  WARNING: PDF had {result.err} error(s). File still saved.")



def save_markdown(text: str, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tailor resume to a JD using Claude AI, export as Markdown + PDF"
    )
    parser.add_argument("--resume", default="input/base_resume.md")
    parser.add_argument("--jd",     default="input/job_description.txt")
    parser.add_argument("--out",    default="output")
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
 
    for path, label in [(args.resume, "Resume"), (args.jd, "Job Description")]:
        if not Path(path).exists():
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)
 
    print("\nResume Tailor -- ATS Optimizer")
    print("-" * 40)
 
    print("Loading files...")
    resume_md = load_file(args.resume)
    jd        = load_file(args.jd)
    print(f"  Resume: {len(resume_md.split())} words | JD: {len(jd.split())} words")
    
    return
     
    print("\nTailoring with Claude AI...")
    tailored_md = tailor_with_ai(resume_md, jd)
    print("  Done.")
 
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(args.out, exist_ok=True)
    md_path  = os.path.join(args.out, f"resume_tailored_{stamp}.md")
    pdf_path = os.path.join(args.out, f"resume_tailored_{stamp}.pdf")
 
    save_markdown(tailored_md, md_path)
    print(f"\nMarkdown -> {md_path}")
 
    if not args.no_pdf:
        print("Generating PDF...")
        md_to_pdf(tailored_md, pdf_path)
        print(f"PDF      -> {pdf_path}")
 
    print("\nDone!\n")
 
 
if __name__ == "__main__":
   
    main()
 