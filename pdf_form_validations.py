from collections import OrderedDict
from PyPDF2 import PdfFileWriter, PdfFileReader
import csv
import os

DIRECTORY = '/Users/lisa/code/Noyo/PDFs'
CSV_FIELD_LIST_FILE_NAME = 'Field_List_NHE.csv'
CSV_OUTPUT_VALIDATION_FILE_NAME = 'validation_fails.csv'
# CSV_FILE_NAME = 'uhc_il_example.csv'  # not currently using
# PDF_FILE_NAME = 'uhc_il_new_hire.pdf'  # not currently using


def _getFields(obj, tree=None, retval=None, fileobj=None):
    """
    Extracts field data if this PDF contains interactive form fields.
    The *tree* and *retval* parameters are for recursive use.

    :param fileobj: A file object (usually a text file) to write
        a report to on all interactive form fields found.
    :return: A dictionary where each key is a field name, and each
        value is a :class:`Field<PyPDF2.generic.Field>` object. By
        default, the mapping name is used for keys.
    :rtype: dict, or ``None`` if form data could not be located.
    """
    fieldAttributes = {'/FT': 'Field Type', '/Parent': 'Parent', '/T': 'Field Name', '/TU': 'Alternate Field Name',
                       '/TM': 'Mapping Name', '/Ff': 'Field Flags', '/V': 'Value', '/DV': 'Default Value'}
    if retval is None:
        retval = OrderedDict()
        catalog = obj.trailer["/Root"]
        # get the AcroForm tree
        if "/AcroForm" in catalog:
            tree = catalog["/AcroForm"]
        else:
            return None
    if tree is None:
        return retval

    obj._checkKids(tree, retval, fileobj)
    for attr in fieldAttributes:
        if attr in tree:
            # Tree is a field
            obj._buildField(tree, retval, fileobj, fieldAttributes)
            break

    if "/Fields" in tree:
        fields = tree["/Fields"]
        for f in fields:
            field = f.getObject()
            obj._buildField(field, retval, fileobj, fieldAttributes)

    return retval


def get_form_fields(infile):
    """Given PDF file, returns ordered dict of field list."""
    infile = PdfFileReader(open(infile, 'rb'))
    fields = _getFields(infile)
    return OrderedDict((k, v.get('/V', '')) for k, v in fields.items())


def update_form_values(infile, outfile, newvals=None):
    """Given an input file, and form field values, write to output file"""
    pdf = PdfFileReader(open(infile, 'rb'))
    writer = PdfFileWriter()

    for i in range(pdf.getNumPages()):
        page = pdf.getPage(i)
        try:
            if newvals:
                writer.updatePageFormFieldValues(page, newvals)
            else:
                writer.updatePageFormFieldValues(page,
                                                 {k: '{i}: {k}'.format(i=i, k=k, v=v)
                                                  for i, (k, v) in enumerate(get_form_fields(infile).items())
                                                  })
            writer.addPage(page)
        except Exception as e:
            print(repr(e))
            writer.addPage(page)

    with open(outfile, 'wb') as out:
        writer.write(out)
    print "values updated in", outfile


def get_field_inputs(filename):
    """Returns a set of field names and required filenames from a csv file."""
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        field_list = set()
        required_field_list = set()
        for row in reader:
            field_list.add(row[0])
            if row[1] == 'Yes':
                required_field_list.add(row[0])
    return [field_list, required_field_list]


def get_field_list(filename):
    """Returns a dictionary of fields to values from a csv file."""
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        field_mapping = {}
        for row in reader:
            field_mapping[row[0]] = row[1]
    return field_mapping


def validate_form_fields(form_fields, field_list, pdf_file_name, required_field_list=None):
    """
    Given form fields and a field list, prints any missing fields to csv.
    If required_field_list, checks that form fields include items from required
    list.
    """
    list_of_form_fields = form_fields.keys()
    for item in list_of_form_fields:
        if item not in field_list:
            print item, "is missing from form fields"
            with open(CSV_OUTPUT_VALIDATION_FILE_NAME, 'a') as file_name:
                writer = csv.writer(file_name, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow([pdf_file_name, item, 'Missing from form fields'])
    # Optional Validation for required fields in PDF that every carrier should have
    if required_field_list:
        print "CHECKING FOR REQUIRED FIELDS IN PDF"
        for field_name in required_field_list:
            if field_name not in list_of_form_fields:
                print field_name, "is not in the PDF, but it's required"
                with open(CSV_OUTPUT_VALIDATION_FILE_NAME, 'a') as file_name:
                    writer = csv.writer(file_name, delimiter=',',
                                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([pdf_file_name, field_name, 'Missing required field'])


def loop_through_pdfs(file_directory, field_list, required_field_list=None):
    """Given directory path of PDF files, loop through to validate."""
    # Clear out CSV file and add headers
    with open(CSV_OUTPUT_VALIDATION_FILE_NAME, 'wb') as file_name:
        writer = csv.writer(file_name, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['pdf_name', 'field_name', 'validation_error'])
    for file_name in os.listdir(file_directory):
        if not file_name.endswith(".pdf"):
            continue
        pdf_file_name = 'PDFs/' + file_name
        print "VALIDATING", pdf_file_name
        try:
            form_fields = get_form_fields(pdf_file_name)
            validate_form_fields(form_fields, field_list, pdf_file_name[5:], required_field_list)
        except AttributeError:
            print pdf_file_name, "did not validate properly"


def populate_PDF_with_field_names(csv_file_name, pdf_file_name):
    """Populate PDF with field names from cvs file."""
    field_mapping = get_field_list(csv_file_name)
    print "UPDATING FORM VALUES"
    update_form_values(pdf_file_name, 'out-' + pdf_file_name)  # enumerate & fill the fields with their own names
    update_form_values(pdf_file_name, 'output-' + pdf_file_name, field_mapping)  # update the form fields


if __name__ == '__main__':
    #populate field list from cvs file
    field_list, required_field_list = get_field_inputs(CSV_FIELD_LIST_FILE_NAME)
    loop_through_pdfs(DIRECTORY, field_list)  ### add in required field list once csv is updated

    # populate_PDF_with_field_names(CSV_FILE_NAME, PDF_FILE_NAME)  # not currently using
