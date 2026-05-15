from itsdangerous import URLSafeTimedSerializer
secret_key='OTP0404'
salt='otpverify'
def endata(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data,salt=salt)              # .dumps Use for endata Encryption
def dndata(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.loads(data,salt=salt)              # .loads Use for dndata Encryption
