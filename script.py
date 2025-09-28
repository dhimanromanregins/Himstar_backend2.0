import requests

user_data = [
    {'username': 'w0rja83w', 'fullName': 'Chris Brown', 'email': 'w0rja83w@outlook.com', 'zipcode': '134456', 'dob': '1954-11-08', 'phonenumber': '8106222893', 'gender': 'male', 'password': 'PxgkMDGN', 'confirm_password': 'PxgkMDGN'},
    {'username': '0k17b3k9', 'fullName': 'Morgan Davis', 'email': '0k17b3k9@outlook.com', 'zipcode': '400434', 'dob': '1983-12-28', 'phonenumber': '8554994970', 'gender': 'female', 'password': 'sRR1Keqb', 'confirm_password': 'sRR1Keqb'},
    {'username': 'x2jfsa63', 'fullName': 'Alex Johnson', 'email': 'x2jfsa63@yahoo.com', 'zipcode': '311256', 'dob': '1977-10-14', 'phonenumber': '1252066034', 'gender': 'other', 'password': 'fqL07A3u', 'confirm_password': 'fqL07A3u'},
    {'username': '2jg5x032', 'fullName': 'Alex Miller', 'email': '2jg5x032@gmail.com', 'zipcode': '145604', 'dob': '1993-05-13', 'phonenumber': '1468068210', 'gender': 'other', 'password': '0PfAmrWb', 'confirm_password': '0PfAmrWb'},
    {'username': 'nnu1z99b', 'fullName': 'Jane Anderson', 'email': 'nnu1z99b@hotmail.com', 'zipcode': '194058', 'dob': '1999-07-16', 'phonenumber': '2244943306', 'gender': 'female', 'password': 'ryqpDRjV', 'confirm_password': 'ryqpDRjV'},
    {'username': '6j9ywgng', 'fullName': 'Morgan Anderson', 'email': '6j9ywgng@yahoo.com', 'zipcode': '237293', 'dob': '1960-07-31', 'phonenumber': '7902298885', 'gender': 'male', 'password': 'c0sAQwC2', 'confirm_password': 'c0sAQwC2'},
    {'username': 'g6lsqvsp', 'fullName': 'Alex Anderson', 'email': 'g6lsqvsp@outlook.com', 'zipcode': '763389', 'dob': '1956-06-29', 'phonenumber': '5010997871', 'gender': 'male', 'password': 'zc2rKj0l', 'confirm_password': 'zc2rKj0l'},
    {'username': '6jzf1k4q', 'fullName': 'Taylor Miller', 'email': '6jzf1k4q@hotmail.com', 'zipcode': '010786', 'dob': '1996-12-13', 'phonenumber': '7566819767', 'gender': 'other', 'password': 'CgWbJJLQ', 'confirm_password': 'CgWbJJLQ'},
    {'username': 'vswbl7ox', 'fullName': 'Jane Davis', 'email': 'vswbl7ox@hotmail.com', 'zipcode': '348748', 'dob': '1998-04-19', 'phonenumber': '0307343845', 'gender': 'female', 'password': 'KdcRyyJG', 'confirm_password': 'KdcRyyJG'},
    {'username': 'upxiyz44', 'fullName': 'Taylor Taylor', 'email': 'upxiyz44@outlook.com', 'zipcode': '524320', 'dob': '1999-09-05', 'phonenumber': '4848447234', 'gender': 'other', 'password': 'ZMnsqkM0', 'confirm_password': 'ZMnsqkM0'},
    {'username': 'h2xb627n', 'fullName': 'Alex Johnson', 'email': 'h2xb627n@hotmail.com', 'zipcode': '922531', 'dob': '1977-01-31', 'phonenumber': '3031844139', 'gender': 'other', 'password': 'SS1fNmfp', 'confirm_password': 'SS1fNmfp'},
    {'username': 'l7a2ejrf', 'fullName': 'Jamie Anderson', 'email': 'l7a2ejrf@gmail.com', 'zipcode': '285077', 'dob': '1983-05-16', 'phonenumber': '2712466340', 'gender': 'female', 'password': '6kANmxMn', 'confirm_password': '6kANmxMn'},
    {'username': 'qlsbdqbq', 'fullName': 'Jamie Davis', 'email': 'qlsbdqbq@gmail.com', 'zipcode': '928739', 'dob': '1975-11-29', 'phonenumber': '2113715073', 'gender': 'female', 'password': 'UWJTCR7j', 'confirm_password': 'UWJTCR7j'},
    {'username': '14yqg1b5', 'fullName': 'Jane Thomas', 'email': '14yqg1b5@hotmail.com', 'zipcode': '485098', 'dob': '1958-03-03', 'phonenumber': '9439303906', 'gender': 'male', 'password': 'qCyng0ky', 'confirm_password': 'qCyng0ky'},
    {'username': '8ld9pame', 'fullName': 'John Anderson', 'email': '8ld9pame@hotmail.com', 'zipcode': '489072', 'dob': '1997-05-11', 'phonenumber': '9440298845', 'gender': 'male', 'password': 'LHEb9RYz', 'confirm_password': 'LHEb9RYz'},
    {'username': 'efc7v6wc', 'fullName': 'Casey Thomas', 'email': 'efc7v6wc@yahoo.com', 'zipcode': '760768', 'dob': '1995-06-19', 'phonenumber': '9605671955', 'gender': 'other', 'password': 'pvxoW6aW', 'confirm_password': 'pvxoW6aW'},
    {'username': 'vh8pqb9s', 'fullName': 'Sam Johnson', 'email': 'vh8pqb9s@outlook.com', 'zipcode': '800805', 'dob': '1985-02-18', 'phonenumber': '2995866136', 'gender': 'male', 'password': 'lwIQl0tn', 'confirm_password': 'lwIQl0tn'},
    {'username': 'alqi7hp1', 'fullName': 'John Miller', 'email': 'alqi7hp1@yahoo.com', 'zipcode': '196379', 'dob': '1989-12-06', 'phonenumber': '7627533142', 'gender': 'male', 'password': 'ioAJvVd9', 'confirm_password': 'ioAJvVd9'},
    {'username': '61tt0z9n', 'fullName': 'Alex Johnson', 'email': '61tt0z9n@gmail.com', 'zipcode': '846065', 'dob': '1974-08-14', 'phonenumber': '2429473648', 'gender': 'female', 'password': '2L5q9mw9', 'confirm_password': '2L5q9mw9'},
    {'username': 'f3jrtuzx', 'fullName': 'Taylor Wilson', 'email': 'f3jrtuzx@outlook.com', 'zipcode': '820219', 'dob': '1992-12-31', 'phonenumber': '8156586285', 'gender': 'other', 'password': '0hOzPwXr', 'confirm_password': '0hOzPwXr'},
    {'username': 'ggeq73v9', 'fullName': 'Jane Thomas', 'email': 'ggeq73v9@yahoo.com', 'zipcode': '080208', 'dob': '1970-09-08', 'phonenumber': '7186173014', 'gender': 'female', 'password': 'TFZZ0mq5', 'confirm_password': 'TFZZ0mq5'},
    {'username': 'pd1v90na', 'fullName': 'Morgan Taylor', 'email': 'pd1v90na@hotmail.com', 'zipcode': '601348', 'dob': '1973-09-14', 'phonenumber': '9912759017', 'gender': 'female', 'password': 'ASAVWHG5', 'confirm_password': 'ASAVWHG5'},
    {'username': 'azmc7gfg', 'fullName': 'Jordan Brown', 'email': 'azmc7gfg@outlook.com', 'zipcode': '672228', 'dob': '1997-09-30', 'phonenumber': '7683413741', 'gender': 'male', 'password': 'uIVCY3Wi', 'confirm_password': 'uIVCY3Wi'},
    {'username': '6axfkruq', 'fullName': 'Jamie Taylor', 'email': '6axfkruq@hotmail.com', 'zipcode': '176350', 'dob': '1998-09-21', 'phonenumber': '8019999018', 'gender': 'female', 'password': 'BfUecv1q', 'confirm_password': 'BfUecv1q'},
    {'username': 'ls79m1iu', 'fullName': 'Sam Brown', 'email': 'ls79m1iu@gmail.com', 'zipcode': '396268', 'dob': '1978-05-15', 'phonenumber': '4733501471', 'gender': 'female', 'password': 'FMbdRuFq', 'confirm_password': 'FMbdRuFq'},
]

def create_users(user_data):
    for user in user_data:
        try:
            response = requests.post('http://192.168.168.200:8000/api/register/', json=user)
            if response.status_code == 201:
                print(f'User {user["username"]} created successfully')
            else:
                print(f'Failed to create user {user["username"]}: {response.status_code} - {response.text}')
        except requests.exceptions.RequestException as e:
            print(f'Error creating user {user["username"]}: {e}')
        break

if __name__ == '__main__':
    create_users(user_data)
