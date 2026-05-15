import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465) #SMTP Port (SSL): 465
    server.login('maheswaripodugu1434@gmail.com','wfuw izkf plms jvfc')
    msg=EmailMessage()
    msg['FROM']='maheswaripodugu1434@gmail.com'
    msg['SUBJECT']=subject
    msg['TO']=to
    msg.set_content(body)
    server.send_message(msg)
    server.close()
    