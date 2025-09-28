import hashlib
import requests

def make_payment():
    api_key = "gsX8Qf"
    salt = "XXK7mLZbLMvtZyIs8KWSqx75s216CioB"
    txn_id = "123"
    amount = "100.00"
    product_info = "Test Product"
    first_name = "John"
    email = "john@example.com"
    phone = "9999999999"
    surl = "http://example.com/success"
    furl = "http://example.com/failure"

    hash_string = f"{api_key}|{txn_id}|{amount}|{product_info}|{first_name}|{email}|||||||||||{salt}"
    hash = hashlib.sha512(hash_string.encode()).hexdigest()

    url = "https://secure.payu.in/_payment"
    payload = {
        "key": api_key,
        "txnid": txn_id,
        "amount": amount,
        "productinfo": product_info,
        "firstname": first_name,
        "email": email,
        "phone": phone,
        "surl": surl,
        "furl": furl,
        "hash": hash
    }

    response = requests.post(url, data=payload)
    print(response.text)

make_payment()