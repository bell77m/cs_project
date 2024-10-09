import logs
import mysql.connector
# import configparser
#
# config_object = configparser.ConfigParser()
#
# config_object["server"]={"port" : "8080", "host" : "127.0.0.1"}
# config_object["logging"]={"level" : "info", "file" : "/var/log/web-server.log"}
# config_object["database"]={"url" : "postgres://user:password@host:port/database", "pool" : "100"}
#
# with open("server-config.ini","w") as file_object:
#     config_object.write(file_object)


class Database(logs.Logs):
    def __init__(self, host="localhost", port=3306, user="root", pwd=""):
        self.mydb = mysql.connector.connect(host=host, user=user, port=port, password=pwd)

    def getDb(self):
        return self.mydb

print(Database(user="bell77m", pwd="237812341"))