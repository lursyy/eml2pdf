"""
Convert email files (.eml) to a single PDF document.

Usage:
    python script.py [input_directory]

Examples:
    python script.py                    # Process .eml files in current directory
    python script.py /path/to/emails    # Process .eml files in specified directory
"""

from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr, getaddresses
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageTemplate, Frame, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def process_emails(input_dir=".", output_file="combined.pdf"):
    """Convert all .eml files in input_dir to a single PDF."""
    
    class PageNumberCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._page_count = 0
        
        def showPage(self):
            self._page_count += 1
            canvas.Canvas.showPage(self)
        
        def save(self):
            total_pages = self._page_count
            self.set_current_page_number(1)
            for page_num in range(1, self._page_count + 1):
                self.draw_page_decorations(page_num, total_pages)
            canvas.Canvas.save(self)
        
        def draw_page_decorations(self, page_num, total_pages):
            pass
    
    def footer_func(canvas, doc, total_pages):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(inch, 0.5*inch, f"Seite {doc.page} von {total_pages}")
        canvas.restoreState()
    
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

    # Create PDF with custom page template for page numbers
    doc = SimpleDocTemplate(output_file, pagesize=A4, bottomMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    total_pages = len(emails)

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
