import os
import PyPDF4 as PyPDF
import pdfplumber as pdfplumber
import fpdf as fpdf

root_directory = "D:\\Downloads\\Business\\Order\\"
# remove file Merge.pdf and Final.pdf
if os.path.exists(root_directory + "Merged.pdf"):
    os.remove(root_directory + "Merged.pdf")
if os.path.exists(root_directory + "Final.pdf"):
    os.remove(root_directory + "Final.pdf")
# merge all the pdf from root_directory
pdf_files = [f for f in os.listdir(root_directory) if f.endswith(".pdf")]
merger = PyPDF.PdfFileMerger()
for filename in pdf_files:
    merger.append(PyPDF.PdfFileReader(root_directory + filename))
merger.write(root_directory + "Merged.pdf")
merger.close()
# setting for new pdf
pdfData = fpdf.FPDF('P', 'mm', 'A5')
pdfData.add_page()
pdfData.set_font('Courier', '', 12)

read = pdfplumber.open(root_directory + 'Merged.pdf')
reader = PyPDF.PdfFileReader(open(root_directory + 'Merged.pdf', 'rb'))
pdfWriter = PyPDF.PdfFileWriter()
product_data = []
product_page = []


def rearrange_serial_numbers(products):
    rearranged_data = {}

    for item in products:
        product_name = item['product_name'].strip()
        variable = item['variable'].strip()
        page = item['page']

        if product_name not in rearranged_data:
            rearranged_data[product_name] = {}

        if variable not in rearranged_data[product_name]:
            rearranged_data[product_name][variable] = []

        rearranged_data[product_name][variable].append(page)

    return rearranged_data


def refining(variable):
    if variable[-1] == 'd':
        variable = variable[:-1]
    return variable


def identifying(data):
    data = ((data.replace(' 2', '').replace('Champange ', '').replace('Rabbit Earphone', 'Rabbit').
            replace('Sky Blue', 'Aqua').replace('(Kn 313)', '').replace('Secon', '').replace('Deep', '').
            replace('Offer', '')).replace('Champagne', '').replace('Pinkd', 'Pink').replace(' 3', '').
            replace('Antique White', 'White').replace('Matte Black', 'Black'))
    if '-' not in data:
        data = data.replace(' ', '-', 1)
    return data


for pageNo in range(len(read.pages)):
    totalOrder = read.pages[pageNo].extract_tables()[0][11][4]
    if totalOrder is None:
        totalOrder = read.pages[pageNo].extract_tables()[0][11][5]
    Total_Orders = int(totalOrder)
    Order_No = read.pages[pageNo].extract_tables()[0][0][1]
    for order_it in range(Total_Orders):
        print(f"Page: {pageNo + 1:<4} Total: {Total_Orders}")
        sellerSKU = read.pages[pageNo].extract_tables()[3][order_it + 1][3]
        Name, Variable = (identifying(sellerSKU.replace('\n', ' ').title()).split('-'))
        Variable = refining(Variable.split('_')[0])
        Name = Name.split('_')[0]
        if Total_Orders > 1:
            Name = Name + ' Multi'
        product_data.append(
            {'product_name': Name, 'variable': Variable, 'page': pageNo})

rearranged_serial_numbers = rearrange_serial_numbers(product_data)
for product, variation in rearranged_serial_numbers.items():
    print(f"Product: {product}")
    pdfData.cell(40, 10, 'Product: ' + product, 0, 1)
    for color, serial_numbers in variation.items():
        print(f"  SKU: {color} Total: {len(serial_numbers)}")
        pdfData.cell(40, 5, '\t\tSKU: ' + color + ' Total: ' + str(len(serial_numbers)), 0, 1)
        product_page.extend(serial_numbers)
product_page = list(dict.fromkeys(product_page))
pdfData.output(root_directory + 'Final.pdf')
reader_Final = PyPDF.PdfFileReader(open(root_directory + 'Final.pdf', 'rb'))
pdfWriter.addPage(reader_Final.getPage(0))
for serial_number in product_page:
    pdfWriter.addPage(reader.getPage(serial_number))
    pdfOutputFile = open(root_directory + '{}.pdf'.format('Final'), 'wb')
    pdfWriter.write(pdfOutputFile)
    pdfOutputFile.close()
read.close()
