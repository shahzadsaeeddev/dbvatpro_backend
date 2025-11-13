from rest_framework import serializers 

class invoiceStep9invoiceLines(serializers.Serializer):
    invoiceNo= serializers.CharField(max_length=200)
    

class invoiceStep10invoiceLines(serializers.Serializer):
    invoiceNo= serializers.CharField(max_length=200)
    invoiceDate= serializers.CharField(max_length=200)


class invoiceStep8invoiceLines(serializers.Serializer):
    id= serializers.CharField(max_length=200)
    invoicedQuantity= serializers.CharField(max_length=200)
    lineExtensionAmount= serializers.CharField(max_length=200)
    taxAmount= serializers.CharField(max_length=200)
    roundingAmount= serializers.CharField(max_length=200)
    itemName= serializers.CharField(max_length=200)
    taxId= serializers.CharField(max_length=200)
    taxPercentage= serializers.CharField(max_length=200)
    taxScheme= serializers.CharField(max_length=200)
    priceAmount= serializers.CharField(max_length=200)
    allowanceChargeReason= serializers.CharField(max_length=200)
    allowanceChargeAmount= serializers.CharField(max_length=200)



class invoiceStep7legalMonetaryTotal(serializers.Serializer):
    lineExtensionAmount= serializers.CharField(max_length=200)
    taxExclusiveAmount= serializers.CharField(max_length=200)
    taxInclusiveAmount= serializers.CharField(max_length=200)
    allowanceTotalAmount= serializers.CharField(max_length=200)
    prepaidAmount= serializers.CharField(max_length=200)
    payableAmount= serializers.CharField(max_length=200)

class invoiceStep6totalTax(serializers.Serializer):
    taxAmount= serializers.CharField(max_length=200)
    tsttaxableAmount= serializers.CharField(max_length=200)
    tsttaxAmount= serializers.CharField(max_length=200)
    taxId= serializers.CharField(max_length=200)
    taxPercentage= serializers.CharField(max_length=200)
    taxScheme= serializers.CharField(max_length=200)

class invoiceStep5allownses(serializers.Serializer):
    chargeIndicator= serializers.CharField(max_length=200)
    allowanceChargeReason= serializers.CharField(max_length=200)
    amount= serializers.CharField(max_length=200)
    taxId= serializers.CharField(max_length=200)
    taxPercentage= serializers.CharField(max_length=200)
    taxScheme= serializers.CharField(max_length=200)

class invoiceStep4customer(serializers.Serializer):
    id= serializers.CharField(max_length=200)
    uuid= serializers.CharField(max_length=200)
    pih = serializers.CharField(max_length=2500)

class invoiceStep3customer(serializers.Serializer):
    id= serializers.CharField(max_length=200)
    streetName= serializers.CharField(max_length=200)
    additionalStreetName=serializers.CharField(max_length=200)
    buildingNumber= serializers.CharField(max_length=200)
    plotIdentification= serializers.CharField(max_length=200)
    citySubdivisionName= serializers.CharField(max_length=200)
    cityName= serializers.CharField(max_length=200)
    postalZone= serializers.CharField(max_length=200)
    companyID= serializers.CharField(max_length=200)
    taxID=  serializers.CharField(max_length=200)
    registrationName= serializers.CharField(max_length=200)
    schema = serializers.CharField(max_length=50)

class invoiceStep2supplier(serializers.Serializer):
    id= serializers.CharField(max_length=200)
    streetName= serializers.CharField(max_length=200)
    buildingNumber= serializers.CharField(max_length=200)
    plotIdentification= serializers.CharField(max_length=200)
    citySubdivisionName= serializers.CharField(max_length=200)
    cityName= serializers.CharField(max_length=200)
    postalZone= serializers.CharField(max_length=200)
    companyID= serializers.CharField(max_length=200)
    taxID=  serializers.CharField(max_length=200)
    registrationName= serializers.CharField(max_length=200)
    schema = serializers.CharField(max_length=50)
    



class invoiceType(serializers.Serializer):
    invoiceType = serializers.CharField(max_length=200)
    documentType = serializers.CharField(max_length=200)


class invoiceStep1(serializers.Serializer):
    invoice=invoiceType()
    profileID= serializers.CharField(max_length=200)
    id=  serializers.CharField(max_length=200)
    uuid= serializers.CharField(max_length=200)
    issueDate= serializers.CharField(max_length=200)
    issueTime= serializers.CharField(max_length=200)
    additionalDocumentReference=invoiceStep4customer()
    accountingSupplierParty=invoiceStep2supplier()
    accountingCustomerParty=invoiceStep3customer()
    paymentMeansCode= serializers.CharField(max_length=10)
    actualDeliveryDate= serializers.CharField(max_length=10)
    allowanceCharge=invoiceStep5allownses()
    taxAmount= serializers.CharField(max_length=10)
    taxTotal=invoiceStep6totalTax()
    legalMonetaryTotal=invoiceStep7legalMonetaryTotal()
    invoiceLines = invoiceStep8invoiceLines(many=True)
        
    
    def create(self, validated_data):
        
        return validated_data



class debitNote1(serializers.Serializer):
    profileID= serializers.CharField(max_length=200)
    id=  serializers.CharField(max_length=200)
    uuid= serializers.CharField(max_length=200)
    issueDate= serializers.CharField(max_length=200)
    issueTime= serializers.CharField(max_length=200)
    billingReference=invoiceStep10invoiceLines()
    additionalDocumentReference=invoiceStep4customer()
    accountingSupplierParty=invoiceStep2supplier()
    accountingCustomerParty=invoiceStep3customer()
    paymentMeansCode= serializers.CharField(max_length=10)
    actualDeliveryDate= serializers.CharField(max_length=10)
    allowanceCharge=invoiceStep5allownses()
    taxAmount= serializers.CharField(max_length=10)
    taxTotal=invoiceStep6totalTax()
    legalMonetaryTotal=invoiceStep7legalMonetaryTotal()
    invoiceLines = invoiceStep8invoiceLines(many=True)
        
    
    def create(self, validated_data):
        
        return validated_data




class creditNote1(serializers.Serializer):
    profileID= serializers.CharField(max_length=200)
    id=  serializers.CharField(max_length=200)
    uuid= serializers.CharField(max_length=200)
    issueDate= serializers.CharField(max_length=200)
    issueTime= serializers.CharField(max_length=200)
    billingReference=invoiceStep10invoiceLines()
    additionalDocumentReference=invoiceStep4customer()
    accountingSupplierParty=invoiceStep2supplier()
    accountingCustomerParty=invoiceStep3customer()
    paymentMeansCode= serializers.CharField(max_length=10)
    actualDeliveryDate= serializers.CharField(max_length=10)
    allowanceCharge=invoiceStep5allownses()
    taxAmount= serializers.CharField(max_length=10)
    taxTotal=invoiceStep6totalTax()
    legalMonetaryTotal=invoiceStep7legalMonetaryTotal()
    invoiceLines = invoiceStep8invoiceLines(many=True)
        
    
    def create(self, validated_data):
        
        return validated_data
