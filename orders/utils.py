import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from django.utils import timezone

def draw_background(canvas, doc):
    """Draws a premium top brand bar, bottom divider, and page numbers on the PDF canvas"""
    canvas.saveState()
    # Top primary brand accent bar (Royal Blue #2563eb)
    canvas.setFillColor(colors.HexColor("#2563eb"))
    canvas.rect(36, doc.pagesize[1] - 12, doc.pagesize[0] - 72, 4, fill=True, stroke=False)
    
    # Bottom fine line divider
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.setLineWidth(0.5)
    canvas.line(36, 40, doc.pagesize[0] - 36, 40)
    
    # Footer Details
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(colors.HexColor("#1e293b"))
    canvas.drawString(36, 24, "RIGBUILDER")
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(98, 24, "|   https://rigbuilder.com   |   support@custompcbuilder.com")
    canvas.drawRightString(doc.pagesize[0] - 36, 24, f"Page {doc.page}")
    canvas.restoreState()

def generate_invoice_pdf(order):
    """Generates a beautiful ReportLab PDF invoice and returns it as a bytes stream"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=36, 
        leftMargin=36, 
        topMargin=40, 
        bottomMargin=55
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor("#0f172a") # Slate 900
    border_color = colors.HexColor("#cbd5e1") # Slate 300
    text_color = colors.HexColor("#334155") # Slate 700
 
    # Custom Paragraph Styles
    logo_style = ParagraphStyle(
        'InvoiceLogo',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'InvoiceHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#475569")
    )
    
    meta_style = ParagraphStyle(
        'InvoiceMetaRight',
        parent=styles['Normal'],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=2 # Right align
    )
    
    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=text_color
    )
    
    bold_body_style = ParagraphStyle(
        'InvoiceBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    bold_white_style = ParagraphStyle(
        'BoldWhite',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    bold_white_style_center = ParagraphStyle(
        'BoldWhiteCenter',
        parent=bold_white_style,
        alignment=1 # Center
    )
    bold_white_style_right = ParagraphStyle(
        'BoldWhiteRight',
        parent=bold_white_style,
        alignment=2 # Right
    )
    
    body_style_center = ParagraphStyle(
        'BodyCenter',
        parent=body_style,
        alignment=1 # Center
    )
    body_style_right = ParagraphStyle(
        'BodyRight',
        parent=body_style,
        alignment=2 # Right
    )

    # 1. Header Section (Company logo and invoice metadata)
    header_data = [
        [
            Paragraph("<b>RIG<font color='#2563eb'>BUILDER</font></b><br/><font size=8 color='#64748b'>High-End Gaming Rigs & Workstations</font>", logo_style),
            Paragraph("<font size=18 color='#2563eb'><b>QUOTATION INVOICE</b></font><br/>"
                      f"<b>Invoice No:</b> {order.invoice.invoice_number if hasattr(order, 'invoice') and order.invoice else 'QUO-' + order.order_number[-6:]}<br/>"
                      f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d')}<br/>"
                      f"<b>Payment:</b> <font color='#16a34a'><b>{order.status.upper()}</b></font>", meta_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. Billing & Shipping Details Card
    billing_text = "<b>BILL TO:</b><br/>" + order.billing_address.replace('\n', '<br/>')
    shipping_text = "<b>SHIP TO:</b><br/>" + order.shipping_address.replace('\n', '<br/>')
    
    address_data = [
        [
            Paragraph(billing_text, body_style),
            Paragraph(shipping_text, body_style)
        ]
    ]
    address_table = Table(address_data, colWidths=[265, 265])
    address_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(address_table)
    story.append(Spacer(1, 15))

    # 3. Selected Components / Product Grid
    grid_data = [
        [
            Paragraph("<b>Item Description</b>", bold_white_style),
            Paragraph("<b>Qty</b>", bold_white_style_center),
            Paragraph(f"<b>Unit Price ({order.country.currency.code})</b>", bold_white_style_right),
            Paragraph(f"<b>Total ({order.country.currency.code})</b>", bold_white_style_right)
        ]
    ]
    
    rate = order.country.currency.exchange_rate_to_usd
    symbol = order.country.currency.symbol
    
    for item in order.items.all():
        name = item.product.name if item.product else (item.pc_build.name if item.pc_build else "Custom Configuration")
        brand = item.product.brand.name if item.product else "Custom Build"
        desc = f"<b>{brand}</b> - {name}"
        
        unit_price_local = item.price_local
        total_price_local = unit_price_local * item.quantity
        
        grid_data.append([
            Paragraph(desc, body_style),
            Paragraph(str(item.quantity), body_style_center),
            Paragraph(f"{symbol} {unit_price_local:.2f}", body_style_right),
            Paragraph(f"{symbol} {total_price_local:.2f}", body_style_right)
        ])
        
    grid_table = Table(grid_data, colWidths=[300, 40, 100, 100])
    
    # Base table formatting
    grid_style = [
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ]
    # Zebra striping for alternating rows
    for i in range(1, len(grid_data)):
        bg = colors.HexColor("#ffffff") if i % 2 != 0 else colors.HexColor("#f8fafc")
        grid_style.append(('BACKGROUND', (0, i), (-1, i), bg))
        
    grid_table.setStyle(TableStyle(grid_style))
    story.append(grid_table)
    story.append(Spacer(1, 15))

    # 4. Financial Calculations Block
    subtotal_local = order.subtotal_usd * rate
    discount_local = order.discount_usd * rate
    tax_local = order.tax_usd * rate
    shipping_local = order.shipping_usd * rate
    grand_total_local = order.grand_total_usd * rate

    financial_data = [
        [Paragraph("Subtotal:", body_style_right), Paragraph(f"<b>{symbol} {subtotal_local:.2f}</b>", body_style_right)],
        [Paragraph("Coupon Discount:", body_style_right), Paragraph(f"- {symbol} {discount_local:.2f}", body_style_right)],
        [Paragraph(f"GST / Tax ({order.country.default_tax_rate}%):", body_style_right), Paragraph(f"{symbol} {tax_local:.2f}", body_style_right)],
        [Paragraph("Shipping Charge:", body_style_right), Paragraph(f"{symbol} {shipping_local:.2f}", body_style_right)],
        [Paragraph("<font size=11 color='#1e293b'><b>Grand Total:</b></font>", body_style_right), Paragraph(f"<font size=11 color='#2563eb'><b>{symbol} {grand_total_local:.2f}</b></font>", body_style_right)]
    ]
    
    fin_table = Table(financial_data, colWidths=[380, 160])
    fin_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor("#cbd5e1")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, -1), (-1, -1), 1, colors.HexColor("#e2e8f0")),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 20))

    # 5. Terms and Real QR Code
    qr_widget = QrCodeWidget(f"http://127.0.0.1:8000/orders/track/{order.order_number}")
    qr_widget.barWidth = 65
    qr_widget.barHeight = 65
    qr_drawing = Drawing(65, 65)
    qr_drawing.add(qr_widget)
    
    terms_text = (
        "<b>Terms & Conditions:</b><br/>"
        "1. All custom built gaming rigs include a standard 3-year parts & labor warranty.<br/>"
        "2. This quotation is valid for 30 days from the invoice date.<br/>"
        "3. Goods once sold cannot be returned unless verified defective under warranty.<br/>"
        "<i>For support, please contact support@custompcbuilder.com.</i>"
    )
    
    footer_data = [
        [
            Paragraph(terms_text, body_style),
            qr_drawing
        ]
    ]
    footer_table = Table(footer_data, colWidths=[430, 110])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(footer_table)

    # Build the document with canvas header and footer background
    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val

