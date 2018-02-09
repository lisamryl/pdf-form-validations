# PDF Form Validation

## Description

The script will run validations on all PDF files at the specified directory (PDFs need to be stored in a /PDFs folder). For now, it's not running a validation on required fields, but that feature can easily be added once the CSV file is up to date with that information.

Commented out is code to take in a CSV file with field names and values and output a PDF.


## How to Run PDF Validations

* Git clone into a new folder
* Set up a virtual environment (e.g. "virtualenv env")
* Activate it (e.g. source/env/bin/activate)
* Install all requirements (e.g. pip install -r requirements.txt)
* Update the directory path name and csv field file name in the script, if necessary.
* Run python pdf_form_validations.py

## Notes

* When "Required" column is filled out, replace:
loop_through_pdfs(DIRECTORY, field_list)
with
loop_through_pdfs(DIRECTORY, field_list, required_field_list)
