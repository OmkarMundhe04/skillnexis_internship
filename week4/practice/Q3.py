import smtplib as sm
server = sm.SMTP("smtp.gmail.com",587)
server.starttls()

sender_email = "omkarmundhexx@gmail.com"
password = "xxxx xxxx xxxx xxxx"
server.login(sender_email,password)

receiver_email = "abhiaadavxx@gmail.com"
subject = "Test Email"
body="This is an email for testing smtp in python"

message=f"subject : {subject} \n\n {body}"
server.sendmail(sender_email,receiver_email,message)
server.quit()
