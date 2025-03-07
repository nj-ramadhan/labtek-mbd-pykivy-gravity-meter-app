import requests

SERVER = 'https://app.kickyourplast.com/api/'
MACHINE_CODE = 'KYP001'

text_coupon = "\n\tKVX4RCNRT\n\n"
text_coupon = text_coupon.replace("\n","")
text_coupon = text_coupon.replace("\t","")

if (text_coupon != ""):
    try :
        r = requests.post(SERVER + 'transactions/' + text_coupon + '/used_machine', data={'machine_code' : MACHINE_CODE})
        print(r)
        status = r.json()['status']
        message = r.json()['message']

        if (status == "success"):
            endpoint = f'{SERVER}transaction_by_code/{text_coupon}'
            print(endpoint)
            r = requests.get(endpoint.strip())
            cold = False if (r.json()['transaction_details'][0]['drink_type']=='regular') else True
            product = r.json()['transaction_details'][0]['size']
            print("Success! Fit your tumbler then press Start")

        else:
            print(status, message)

    except Exception as e:
        print(status, message)
        
text_coupon = False

