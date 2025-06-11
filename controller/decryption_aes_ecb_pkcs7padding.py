import base64
from Crypto.Cipher import AES

def decrypt(key, decrData):
    unpad = lambda date: date[0:-ord(date[-1])]
    res = base64.decodebytes(decrData.encode("utf8"))
    aes = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    msg = aes.decrypt(res).decode("utf8")
    return unpad(msg)