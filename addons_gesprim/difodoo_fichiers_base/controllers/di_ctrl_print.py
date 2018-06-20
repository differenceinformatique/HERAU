# -*- coding: utf-8 -*-

from odoo import models,fields,api,http
#from . import models,wizards
import os, sys
import win32print

# class MyController(http.Controller):
#     @http.route(type='json', website=True)
#     def imp_javascript(self,data, **kw):
# 
#       #Fetch input json data sent from js
#         openWin(data)
#        # Your code is here 



def format_data(labelmodelfile,charSep,parameters):
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
    
    return contenu 
        
        
    

      
def printlabelonwindows(printer,contenu):
    if sys.version_info >= (3,):
        raw_data = bytes(contenu,"utf-8")
    else:
        raw_data = contenu 
               
#     execute_js('./difodoo/addons_gesprim/difodoo_fichiers_base/script/di_impression_client.js')
#     function openWin() {
#     var printWindow = window.open();
#     printWindow.document.open('text/plain')
#     printWindow.document.write('${raw_data}$');
#     printWindow.document.close();
#     printWindow.focus();
#     printWindow.print();
#   }
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