# -*- coding: utf-8 -*-

from odoo import models,fields,api
#from . import models,wizards
import os, sys
import win32print


def printlabelonwindows(printer,labelmodelfile,charSep,parameters):
    
    
    
    contenu = "";
    with open(labelmodelfile) as fichierEtiq:
        for line in fichierEtiq:
            contenu += line + "\r\n"
    
    for paramName,value in parameters:
           
        if contenu.find(charSep + paramName.lower() + charSep) != -1:
            if (value is not None):
                contenu = contenu.replace(charSep + paramName.lower() + charSep, str(value).replace("é", "\\82").replace("à", "\\85").replace("î","\\8C"))
            else:
                contenu = contenu.replace(charSep + paramName.lower() + charSep, "")
    #print(sys.version_info)    
      
    if sys.version_info >= (3,):
        raw_data = bytes(contenu,"utf-8")
    else:
        raw_data = contenu
      
#     printer_name = win32print.GetDefaultPrinter ()  
    hPrinter = win32print.OpenPrinter (printer)
#    hPrinter = win32print.OpenPrinter (printer_name)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("print", None, "RAW"))
        try:
            win32print.StartPagePrinter (hPrinter)
            win32print.WritePrinter (hPrinter, raw_data)
            win32print.EndPagePrinter (hPrinter)
        finally:
            win32print.EndDocPrinter (hPrinter)
    finally:
        win32print.ClosePrinter (hPrinter)

def callFonction(self):
    return