from .models import BankAccount
from pathlib import Path
from reportlab.platypus import Image, Spacer
from io import BytesIO
from xml.sax.saxutils import escape
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from .context_processors import company


def generate_invoice_pdf(invoice):
    b = BytesIO()

    doc = SimpleDocTemplate(
        b,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    small = ParagraphStyle(
        "smallL",
        parent=normal,
        fontSize=9,
        leading=13
    )

    title = ParagraphStyle(
        "headingL",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#142d4e")
    )

    c = company(None)["company"]

    # Get active bank account from Django database
    bank = (
        BankAccount.objects
        .filter(is_active=True)
        .order_by("id")
        .first()
    )

    if bank:
        c["bank_name"] = bank.bank_name
        c["bank_account_name"] = bank.account_name
        c["bank_account_number"] = bank.account_number
    else:
        # Do not show placeholder bank details
        c["bank_name"] = ""
        c["bank_account_name"] = ""
        c["bank_account_number"] = ""


    P = lambda v: Paragraph(
        escape(str(v or "")),
        small
    )

    # PDF content
    elements = []

    # -------------------------
    # COMPANY LOGO
    # -------------------------
    logo_path = (
        Path(settings.BASE_DIR)
        / "static"
        / "images"
        / "luztow-logo.png"
    )

    if logo_path.exists():
        logo = Image(
            str(logo_path),
            width=120,
            height=70
        )
        logo.hAlign = "LEFT"

        elements.append(logo)
        elements.append(Spacer(1, 10))

    # -------------------------
    # COMPANY INFORMATION
    # -------------------------
    elements.append(
        Paragraph(
            escape(c["name"].upper()),
            title
        )
    )

    elements.append(
        Paragraph("INVOICE", styles["Heading2"])
    )

    elements.append(Spacer(1, 10))

    for key in ["address", "phone", "email", "tax_id"]:
        if c.get(key):
            label = "Tax ID: " if key == "tax_id" else ""
            elements.append(P(label + c[key]))

    elements.append(Spacer(1, 12))

    # -------------------------
    # INVOICE INFORMATION
    # -------------------------
    invoice_details = [
        f"Invoice: {invoice.number}",
        f"Issued: {invoice.issue_date}",
        f"Due: {invoice.due_date}",
        f"Status: {invoice.get_status_display()}",
        f"Bill to: {invoice.customer.name}",
        invoice.customer.address,
        invoice.customer.email,
    ]

    for line in invoice_details:
        if line:
            elements.append(P(line))
            elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 10))

    # -------------------------
    # INVOICE ITEMS
    # -------------------------
    data = [[
        P("Description"),
        P("Qty"),
        P("Unit price (NGN)"),
        P("Amount (NGN)")
    ]]

    for item in invoice.items.all():
        data.append([
            P(item.description),
            P(item.quantity),
            P(f"{item.unit_price:,.2f}"),
            P(f"{item.line_total:,.2f}")
        ])

    # -------------------------
    # INVOICE TOTALS
    # -------------------------
    vat_label = (
    "VAT (7.5% on Service Charge)"
    if invoice.apply_vat
    else "VAT (Not Applied)"
)

    totals = [
        ("Subtotal", invoice.subtotal),
        (vat_label, invoice.vat_amount),
        ("TOTAL", invoice.total),
        ("Paid", invoice.amount_paid),
        ("Balance", invoice.balance),
    ]

    for label, value in totals:
        data.append([
            "",
            "",
            P(label),
            P(f"{value:,.2f}")
        ])

    # -------------------------
    # TABLE DESIGN
    # -------------------------
    t = Table(
        data,
        colWidths=[180, 45, 110, 110],
        repeatRows=1,
        hAlign="LEFT"
    )

    t.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#142d4e")
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                colors.white,
                colors.HexColor("#f3f6fa")
            ]
        ),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.3,
            colors.HexColor("#d5dce5")
        ),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    elements.append(t)
    elements.append(Spacer(1, 16))

    # -------------------------
    # PAYMENT DETAILS
    # -------------------------
    
    # -------------------------
    # BANK PAYMENT DETAILS
    # -------------------------
    if c.get("bank_name") and c.get("bank_account_number"):

        elements.append(Spacer(1, 15))

        elements.append(
            Paragraph("BANK PAYMENT DETAILS", styles["Heading3"])
        )

        bank_details = [
            ("Bank Name", c.get("bank_name")),
            ("Account Name", c.get("bank_account_name")),
            ("Account Number", c.get("bank_account_number")),
        ]

        for label, value in bank_details:
            if value:
                elements.append(P(f"{label}: {value}"))

        elements.append(Spacer(1, 10))
        elements.append(
            P("Please use your invoice number as payment reference.")
        )


    # -------------------------
    # NOTES
    # -------------------------
    if invoice.notes:
        elements.append(Spacer(1, 10))
        elements.append(P("Notes: " + invoice.notes))

    # -------------------------
    # GENERATE PDF
    # -------------------------
    doc.build(elements)

    b.seek(0)

    return b
