import subprocess
import time
from base64 import b64encode

import os
script_dir = os.path.dirname(os.path.abspath(__file__))

def pro_create_key():
    command = 'openssl'
    args = ['ecparam', '-name', 'secp256k1', '-genkey', '-noout', '-out', os.path.join(script_dir, "file",'PrivateKey.pem')]
    args_2 = ['ec', '-in', os.path.join(script_dir, "file",'PrivateKey.pem'), '-pubout', '-conv_form', 'compressed', '-out', os.path.join(script_dir, "file",'PublicKey.pem')]
    args_3 = ['base64', '-d', '-in', os.path.join(script_dir, "file",'PublicKey.pem'), '-out', os.path.join(script_dir, "file",'PublicKey.bin')]

    # Run the command

    result = subprocess.run([command] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result2 = subprocess.run([command] + args_2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result3 = subprocess.run([command] + args_3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check for errors
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    elif result2.returncode != 0:
        print(f"Error: {result.stderr}")
    elif result3.returncode != 0:
        print(f"Error: {result.stderr}")

    else:
        print("success")


def create_configuration(**data):
    red = os.path.join(script_dir, "file","default.cnf")
    wrt = os.path.join(script_dir, "file", "openssl.cnf")
    f = open(red, 'r')
    filedata = f.read()
    filedata = filedata.replace("C=C", "C=SA")
    filedata = filedata.replace("O=O", "O=" + str(data['O']))
    filedata = filedata.replace("OU=OU", "OU=" + str(data['OU']))
    filedata = filedata.replace("CN=CN", "CN=" + str(data['CN']))
    filedata = filedata.replace("SN=SNS", "SN=" + str(data['SN']))
    filedata = filedata.replace("TYPE=TYPE", str(data['TYPE']))

    filedata = filedata.replace("UID=UUIDS", "UID=" + str(data['UID']))
    filedata = filedata.replace("title=titles", "title=" + str(data['title']))
    filedata = filedata.replace("registeredAddress=Zatca", "registeredAddress=" + str(data['registeredAddress']))
    filedata = filedata.replace("businessCategory=Zatca", "businessCategory=" + str(data['business']))
    with open(wrt, 'w') as t:
        t.write(filedata)
    f.close()


def create_csr(**data):
    pro_create_key()
    create_configuration(**data)


    command = [
        "openssl", "req", "-new", "-sha256",
        "-key",os.path.join(script_dir, "file", "PrivateKey.pem"),
        "-extensions", "v3_req",
        "-config", os.path.join(script_dir, "file","openssl.cnf"),
        "-out", os.path.join(script_dir, "file","cert.csr")
    ]
    # Execute the command
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check the result


    time.sleep(.5)
    f = open(os.path.join(script_dir, "file","cert.csr"), "r")
    pvt = open(os.path.join(script_dir, "file","PrivateKey.pem"), "r")
    pbl = open(os.path.join(script_dir, "file","PublicKey.pem"), "r")
    basestr = b64encode(bytes(str(f.read()), 'utf-8')).decode('utf-8')
    ts = {"status":200,"csr": basestr, "pvt": str(pvt.read()[31:-30]).replace('\n',''), "pbl": str(pbl.read()[27:-25]).replace('\n','')}
    return ts
