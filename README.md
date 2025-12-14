# 💼 Dbvat Pro ZATCA Middleware

> **Enterprise-grade ZATCA Middleware** built for real-world business invoicing and compliance.

A complete **middleware solution for ZATCA integration**, enabling users to **create business profiles, manage customers, and generate ZATCA-compliant invoices** directly from a **user-friendly dashboard**.

---

## ✨ Features at a Glance

- 🔐 **User Authentication**  
  - Login via **Email/Password** or **Google OAuth**  
  - Secure API access for each user  

- 🏢 **Company Profile Setup**  
  - Create and configure your **company profile** for ZATCA  
  - OTP validation for **Sandbox** or **Production**  
  - Includes **Company**, **EGS**, and **Supplier Information**  

- 🛡️ **EGS & Compliance**  
  - Automatically generates **CSR (Certificate Signing Request)**  
  - CSID generated via **ZATCA Compliance API**  
  - Compliance XML documents submitted automatically  
  - Generates **X509 production certificate**  

- 👥 **Customer Management**  
  - Create and manage customers via API  
  - Required fields: street, building, city, VAT number, tax scheme  

- 🧾 **Invoice Management**  
  - Generate invoices (**Standard & Simplified**) and **Credit/Debit Notes**  
  - Includes invoice lines, quantity, price, tax, discount, and payment method  
  - Each invoice provides **Base64 XML string** and **QR code**  

- 🔗 **API Integration**  
  - Fully RESTful API endpoints  
  - Postman collection available for testing  
  - Authentication via **API Key & Secret**  

---

## 🔐 Authentication & Onboarding Flow

1️⃣ **User Login / Registration**  
- Login via **Google OAuth** or **Email/Password**  
- Authentication handled via **Keycloak**  

2️⃣ **Company Profile Setup**  
- Fill in **Company Information** (Name, Address, City, Phone)  
- Configure **EGS Information** for CSR and ZATCA compliance  
- Add **Supplier Information** (CRN, Street, Tax Scheme, Postal Code)  

3️⃣ **OTP Validation**  
- Sandbox OTP: `123345`  
- Production OTP: Obtain from [Fatoora Portal](https://fatoora.zatca.gov.sa/)  

4️⃣ **Dashboard Redirect**  
- After setup, user is redirected to the **main dashboard**  

---

## 📊 Dashboard & Workflow Overview

- 🏢 **Company Management**: View and update company information, manage EGS and supplier details  
- 👥 **Customer Management**: Add new customers via API with required fields (street, building, city, VAT, tax scheme)  
- 🧾 **Invoice Management**: Create invoices with multiple lines and payment methods, supports Standard/Simplified invoices and Credit/Debit Notes, automatic generation of QR codes and XML strings, track invoice status and validation  

---

## ⚡ API Key & Authentication

- Navigate to **API Credentials** after company setup  
- Copy **API Key** and **Secret**  
- Include in all API requests for authentication  

**Headers Example:**

Authorization: Api-Key <YOUR_API_KEY>
Secret: <YOUR_SECRET_KEY>

perl
Copy code

---

## 🧾 Customer & Invoice API Example

**Customer API:**

- **Endpoint:** `POST https://api.dbvat.pro/customer/`  
- **Required Fields:** `street_name`, `building_number`, `city_name`, `city_sub_division_name`, `postal_zone`, `registered_name`, `vat_number`, `tax_scheme`  

**Invoice API:**

- **Endpoint:** `POST https://api.dbvat.pro/invoices-create/`  
- **Invoice Types:** Standard, Simplified, Credit Note, Debit Note  
- **Required Fields:** Invoice lines, product name, quantity, price, tax, discount, invoice number, date, payment method, document type, customer ID


## 🧾 Tech Stack

- Backend: Django REST Framework, Celery, Redis

- Authentication: Keycloak

- Database: PostgreSQL

- Frontend: React.js, Ant Design

- Deployment: Docker

**Combined Example cURL:**

```bash
# Create Customer
curl --location 'https://api.dbvat.pro/customer/' \
--header 'Authorization: Api-Key YOUR_API_KEY' \
--header 'Secret: YOUR_SECRET_KEY' \
--header 'Content-Type: application/json' \
--data '{
  "street_name": "Jab e Zyton",
  "building_number": "1234A",
  "city_subdivision_name": "An Nakheel",
  "city_name": "Riyadh",
  "postal_zone": "12222",
  "registered_name": "string",
  "vat_number": "399999229900003",
  "tax_scheme": "VAT"
}'

# Create Invoice
curl --location 'https://api.dbvat.pro/invoices-create/' \
--header 'Authorization: Api-Key YOUR_API_KEY' \
--header 'Secret: YOUR_SECRET_KEY' \
--header 'Content-Type: application/json' \
--data '{
  "invoice_lines": [{"name": "كتاب","price": "34.00","discount": "0","quantity": "3.0000","tax": "14.85"}],
  "invoice_number": "INV0005",
  "date": "2025-02-08",
  "payment_method": "10",
  "document_types": "Simplified_invoice",
  "customer": "ae22b5b2-ef7c-4c1d-a7eb-020e73131654"
}'
Response includes invoice ID, UUID, XML string, QR code, and validation status.

>For the complete Postman collection  **[Click Here](https://documenter.getpostman.com/view/37631912/2sAYXCjyYD/)** .
