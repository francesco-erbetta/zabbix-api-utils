#!/usr/bin/env python3

# Zabbix Hosts Report Generator

# Requires python3-fpdf https://pypi.org/project/fpdf2/
# fpdf2 tutorial: https://py-pdf.github.io/fpdf2/Tutorial.html
# ubuntu way: apt install python3-fpdf (dont use pip if you can)

import os

# Set paths
base_dir = "repdata"
output_pdf = "report.pdf"

from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Rendering logo:
        self.image("hdr_logo.png", 10, 8, 33)
        # Setting font: helvetica bold 15
        self.set_font("helvetica", style="B", size=15)
        # Calculating width of title and setting cursor position:
        width = self.get_string_width(self.title) + 6
        self.set_x((210 - width) / 2)
        # Setting colors for frame, background and text:
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(173, 216, 230)
        self.set_text_color(220, 50, 50)
        # Setting thickness of the frame (1 mm)
        self.set_line_width(1)
        # Printing title:
        self.cell(
            width,
            9,
            self.title,
            border=1,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
            fill=True,
        )
        # Performing a line break:
        self.ln(10)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        # Setting font: helvetica italic 8
        self.set_font("helvetica", style="I", size=8)
        # Setting text color to gray:
        self.set_text_color(128)
        # Printing page number:
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

# Initialize PDF object
pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=10)
pdf.set_title("Zabbix Weekly Report")
pdf.set_author("BVTECH SpA")

# Insert Cover page
pdf.add_page()
pdf.set_y(100)
pdf.set_font("Helvetica", size=32)
pdf.cell(text="Zabbix Weekly Report",
                new_x="LMARGIN", new_y="NEXT", align='L')
pdf.ln(5)
pdf.set_font("Helvetica", size=24)
pdf.cell(text="Customer: ACME Inc.",
                new_x="LMARGIN", new_y="NEXT", align='L')
pdf.ln(5)
pdf.set_font("Helvetica", size=16)
pdf.cell(text="Date: 26/12/2024",
                new_x="LMARGIN", new_y="NEXT", align='L')

# Iterate through hosts
# Graph must be about 900x200, 3 graphs per page
for host in sorted(os.listdir(base_dir)):
    host_dir = os.path.join(base_dir, host)
    if os.path.isdir(host_dir):
        # Add a new page for the host
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 0, text=f"Host: {host}",
               new_x="LMARGIN", new_y="NEXT", align='L')

        # Add images for the host
        image_count = 0
        for image in sorted(os.listdir(host_dir)):
            if image.endswith(".png"):
                if image_count > 0 and image_count % 3 == 0:
                    pdf.add_page()
                    pdf.set_font("Helvetica", size=12)
                    # Repeat Hostname
                    pdf.cell(0, 0, text=f"Host: {host} (continued)",
                                new_x="LMARGIN", new_y="NEXT", align='L')
                img_path = os.path.join(host_dir, image)
                pdf.image(img_path, x=10, y=pdf.get_y() + 10, w=180)
                pdf.ln(70)  # Adjust space after each image
                image_count += 1
                
# Save PDF
pdf.output(output_pdf)
print(f"Report generated: {output_pdf}")

# Enjoy your report!