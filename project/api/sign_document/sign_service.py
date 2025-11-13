import json
import os
import jpype.imports

jpype.addClassPath('java/zatca_3_2_6.jar')
if not jpype.isJVMStarted():
    jpype.startJVM(jpype.getDefaultJVMPath(), '-ea')


try:

    from com.zatca import integrate
except Exception as e:
    print(jpype.addClassPath())



def sign_xml_document(invoice_xml_base64,private_key,certificate):
    var = integrate().process_sing_document(invoice_xml_base64, private_key, certificate)
    return json.loads(str(var))
