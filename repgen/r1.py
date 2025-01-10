#!/usr/bin/env python3
#
# Zabbix Hosts Report Generator
# Luca Maranzano <liuk@linux.it> - 2024
#
# Requires python3-fpdf https://pypi.org/project/fpdf2/
# fpdf2 tutorial: https://py-pdf.github.io/fpdf2/Tutorial.html

import os
import argparse
from fpdf import FPDF
from datetime import datetime

# Set paths
os.chdir('/home/zabbix-reports/zabbix-api-utils/repgen')
base_dir = "repdata"
output_pdf = "report" + datetime.now().strftime("%Y%m%d") + ".pdf"
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
        self.set_fill_color(200, 220, 255)
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
        self.ln(5)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        # Setting font: helvetica italic 8
        self.set_font("helvetica", style="I", size=8)
        # Setting text color to gray:
        self.set_text_color(128)
        # Printing page number:
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def hostinfo_title(self, num, label):
        # Setting font: helvetica 12
        self.set_font("helvetica", size=14)
        # Setting background color
        self.set_fill_color(200, 220, 255)
        # Printing chapter name:
        self.cell(
            0,
            6,
            f"{num}) Host: {label}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
            fill=True,
        )
        # Performing a line break:
        self.ln(1)

    def hostinfo_body(self, filepath):
        # Reading text file:
        with open(filepath, "rb") as fh:
            txt = fh.read().decode("latin-1")
        # Setting font and size
        self.set_font("helvetica", size=8)
        # Printing justified text:
        #self.multi_cell(0, 5, txt)
        self.write_html(txt)
        # Performing a line break:
        # self.ln(1)
    
    def print_hostinfo(self, num, title, filepath):
        self.add_page()
        self.hostinfo_title(num, title)
        self.hostinfo_body(filepath)

# Define commandline arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Generate PDF from repdata', epilog="""

Usage example:
r1.py "This is my title" "ACME inc" "Last 7 days since today"

""")
parser.add_argument('pdf_title', help='Title string used in header and cover')
parser.add_argument('customer_name', help='Customer name displayed in the cover')
parser.add_argument('time_frame', help='String used in cover about time frame covered by the report')
args = parser.parse_args()

mytitle = args.pdf_title
mycustomer = args.customer_name
mytimeframe = args.time_frame

# Initialize PDF object
pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=10)
# pdf.set_title("Zabbix Weekly Report")
pdf.set_title(mytitle)
pdf.set_author("BVTECH SpA")

# Insert Cover page
pdf.add_page()
pdf.set_y(100)
pdf.set_font("Helvetica", size=32)
pdf.cell(text=mytitle,
                new_x="LMARGIN", new_y="NEXT", align='L')
pdf.ln(5)
pdf.set_font("Helvetica", size=24)
pdf.cell(text="Customer: " + mycustomer,
                new_x="LMARGIN", new_y="NEXT", align='L')
pdf.ln(5)
pdf.set_font("Helvetica", size=14)
pdf.cell(text="Time frame: " + mytimeframe,
                new_x="LMARGIN", new_y="NEXT", align='L')

# Iterate through hosts
# Graph must be about 900x200, 3 graphs per page
host_counter=1
for host in sorted(os.listdir(base_dir)):
    host_dir = os.path.join(base_dir, host)
    host_infofile = os.path.join(host_dir, "info.txt")
    if not os.path.exists(host_infofile):
        print(f"info.txt not found for host {host}. Skipping...")
        continue
    if os.path.isdir(host_dir):
        # Add a new page for the host
        # pdf.add_page()
        # pdf.set_font("Helvetica", size=12)
        # pdf.cell(0, 0, text=f"Host: {host}",
        #        new_x="LMARGIN", new_y="NEXT", align='L')
        pdf.print_hostinfo(host_counter,host, host_infofile)
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
    host_counter +=1
                
# Save PDF
pdf.output(output_pdf)
print(f"Report generated: {output_pdf}")

# Enjoy your report!
