import os
with open("tosend.csv","w+") as f:
    for file in os.listdir("./Studentlogs/Submitted"):
        for line in open("./Studentlogs/Submitted/"+file,"r+"):
            f.write(file.replace(".csv",'')+','+line)
        os.remove("./Studentlogs/Submitted/"+file)
os.system("python emil.py")
