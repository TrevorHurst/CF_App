import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import os
server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

server.login("calfarleyclockin@gmail.com","CENSORED")

message = MIMEMultipart()

message["From"] = "calfarleyclockin@gmail.com"

message["Subject"] = "Clock-in/out Report"

body = "This message was brought to you by Trevor Hurst!"

message.attach(MIMEText(body,"plain"))

with open("tosend.csv", "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
encoders.encode_base64(part)
part.add_header("Content-Disposition",
                f"attachment; filename= {str(datetime.datetime.now())}.csv",)
message.attach(part)
text = message.as_string()


server.sendmail('calfarleyclockin@gmail.com', [i.strip() for i in open("admins.EDITME","r").readlines()]
, text)

os.system(f"MOVE ./tosend.csv ./Studentlogs/Sent/{str(datetime.datetime.now()).replace('.','').replace(' ','').replace(':','')}.csv")
