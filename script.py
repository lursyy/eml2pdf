"""
Convert email files (.eml) to a single PDF document.

Installation:
    Add this alias to your ~/.zshrc or ~/.bashrc:
    alias eml2pdf="source ~/git/eml2pdf/venv/bin/activate && eml2pdf && deactivate"

Usage:
    eml2pdf [input_directory]

Examples:
    eml2pdf              # Process .eml files in current directory
    eml2pdf /path/to/emails    # Process .eml files in specified directory
"""

from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr, getaddresses
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch


def process_emails(input_dir=".", output_file="combined.pdf"):
    """Convert all .eml files in input_dir to a single PDF."""
    emails = []

    for path in Path(input_dir).glob("*.eml"):
        with open(path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)

        date = parsedate_to_datetime(msg["Date"])

        # Prefer plain text body, fall back to HTML
        body = None
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
            if body is None:
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_content()
                        break
        else:
            body = msg.get_content()

        emails.append((date, msg, body))

    if not emails:
        print(f"No .eml files found in {input_dir}")
        return

    emails.sort(key=lambda x: x[0])

    # Create PDF
    doc = SimpleDocTemplate(output_file, pagesize=A4, bottomMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()

    for date, msg, body in emails:
        # Add metadata
        story.append(Paragraph(f"<b>Betreff:</b> {msg['Subject'] or '(no subject)'}", styles['Normal']))
        from_email = parseaddr(msg['From'])[1] if msg['From'] else ''
        to_email = parseaddr(msg['To'])[1] if msg['To'] else ''
        # Handle multiple CC addresses
        cc_value = msg.get('CC') or msg.get('Cc')
        cc_emails = ', '.join([email for _, email in getaddresses([cc_value])]) if cc_value else ''
        
        story.append(Paragraph(f"<b>Datum:</b> {date}", styles['Normal']))
        story.append(Paragraph(f"<b>Von:</b> {from_email}", styles['Normal']))
        story.append(Paragraph(f"<b>An:</b> {to_email}", styles['Normal']))
        if cc_emails:
            story.append(Paragraph(f"<b>CC:</b> {cc_emails}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Add body with line breaks preserved
        if body:
            # Replace newlines with <br/> for proper line breaks
            body_html = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            body_html = body_html.replace("\n", "<br/>")
            story.append(Paragraph(body_html, styles['Normal']))
        
        story.append(PageBreak())

    doc.build(story)
    print(f"PDF created: {output_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
        process_emails(input_dir)
    else:
        process_emails()
