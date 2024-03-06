from flask import Flask
from flask_hashing import Hashing

app = Flask(__name__)
hashing = Hashing(app)

# example password
password = 'test123'

# Encode password 
hashed = hashing.hash_value(password, salt='abcd')
print(hashed)

# Taking user entered password
userPassword = 'test123'

# encoding user password
if hashing.check_value(hashed, userPassword, salt='123'):
    print("Password is Correct")
else:
    print("Password Incorrect")

