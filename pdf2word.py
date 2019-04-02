# gets all files under ROOT_INPUT_PATH with FILE_EXTENSION and tries to extract text from them into ROOT_OUTPUT_PATH with same filename as the input file but with INPUT_FILE_EXTENSION replaced by OUTPUT_FILE_EXTENSION
# https://stackoverflow.com/questions/11341073/how-to-convert-pdf-to-word-using-acrobat-sdk
from win32com.client import Dispatch
from win32com.client.dynamic import ERRORS_BAD_CONTEXT

import winerror

# try importing scandir and if found, use it as it's a few magnitudes of an order faster than stock os.walk
try:
    from scandir import walk
except ImportError:
    from os import walk

import fnmatch

import sys
import os

ROOT_INPUT_PATH = None
ROOT_OUTPUT_PATH = None
INPUT_FILE_EXTENSION = "*.pdf"
OUTPUT_FILE_EXTENSION = ".docx"

def acrobat_extract_text(f_path, f_path_out, f_basename, f_ext):
    avDoc = Dispatch("AcroExch.AVDoc") # Connect to Adobe Acrobat

    # Open the input file (as a pdf)
    ret = avDoc.Open(f_path, f_path)
    assert(ret) # FIXME: Documentation says "-1 if the file was opened successfully, 0 otherwise", but this is a bool in practise?

    pdDoc = avDoc.GetPDDoc()

    dst = os.path.join(f_path_out, ''.join((f_basename, f_ext)))

    # Adobe documentation says "For that reason, you must rely on the documentation to know what functionality is available through the JSObject interface. For details, see the JavaScript for Acrobat API Reference"
    jsObject = pdDoc.GetJSObject()

    # Here you can save as many other types by using, for instance: "com.adobe.acrobat.xml"
    jsObject.SaveAs(dst, "com.adobe.acrobat.docx") # NOTE: If you want to save the file as a .doc, use "com.adobe.acrobat.doc"

    pdDoc.Close()
    avDoc.Close(True) # We want this to close Acrobat, as otherwise Acrobat is going to refuse processing any further files after a certain threshold of open files are reached (for example 50 PDFs)
    del pdDoc

if __name__ == "__main__":
    assert(5 == len(sys.argv)), sys.argv # <script name>, <script_file_input_path>, <script_file_input_extension>, <script_file_output_path>, <script_file_output_extension>

    #$ python get.docx.from.multiple.pdf.py 'C:\input' '*.pdf' 'C:\output' '.docx' # NOTE: If you want to save the file as a .doc, use '.doc' instead of '.docx' here and ensure you use "com.adobe.acrobat.doc" in the jsObject.SaveAs call

    ROOT_INPUT_PATH = sys.argv[1]
    INPUT_FILE_EXTENSION = sys.argv[2]
    ROOT_OUTPUT_PATH = sys.argv[3]
    OUTPUT_FILE_EXTENSION = sys.argv[4]

    # tuples are of schema (path_to_file, filename)
    matching_files = ((os.path.join(_root, filename), os.path.splitext(filename)[0]) for _root, _dirs, _files in walk(ROOT_INPUT_PATH) for filename in fnmatch.filter(_files, INPUT_FILE_EXTENSION))

    # patch ERRORS_BAD_CONTEXT as per https://mail.python.org/pipermail/python-win32/2002-March/000265.html
    global ERRORS_BAD_CONTEXT
    ERRORS_BAD_CONTEXT.append(winerror.E_NOTIMPL)

    for filename_with_path, filename_without_extension in matching_files:
        print("Processing '{}'".format(filename_without_extension))
        acrobat_extract_text(filename_with_path, ROOT_OUTPUT_PATH, filename_without_extension, OUTPUT_FILE_EXTENSION)