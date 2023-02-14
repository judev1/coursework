import bcrypt

password = b'password'

# A randomly generated salt
salt = bcrypt.gensalt()

# The hash produced using my password and the salt
hash = bcrypt.hashpw(password, salt)

print(hash)
