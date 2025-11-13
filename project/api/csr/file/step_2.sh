#!/bin/sh
openssl req -new -sha256 -key PrivateKey.pem -extensions v3_req -config openssl.cnf -out cert.csr



