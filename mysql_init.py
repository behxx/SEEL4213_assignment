import cProfile
import mysql.connector
from sqlalchemy import create_engine

class database:
    def __init__(self):
        self.mydb = mysql.connector.connect(
          host="localhost",
          user="root",
          password="123456",
          database="mydatabase"
        )

        self.mycursor = self.mydb.cursor()

    def create_database(self):
        self.mycursor.execute("CREATE DATABASE mydatabase")

    def create_sensor_table(self):
        self.mycursor.execute("CREATE TABLE senvalues (id INT AUTO_INCREMENT PRIMARY KEY,"
                              "Timestamp VARCHAR(255),"
                              "WaterLevel INT,"
                              "TempValue INT,"
                              "phValue INT)")

    def create_fish_table(self):
        self.mycursor.execute("CREATE TABLE fishdata (id INT AUTO_INCREMENT PRIMARY KEY,"
                              "tagID VARCHAR(255),"
                              "species VARCHAR(255),"
                              "gender VARCHAR(255),"
                              "cageNo VARCHAR(255),"
                              "length FLOAT)")

    def insert_multi_data(self, df):
        engine = create_engine('mysql+mysqlconnector://root:123456@localhost:3306/mydatabase')
        df.to_sql('senvalues', con=engine, if_exists='append', index=False)
        print("Sensor values inserted successfully")
        # Commit the changes
        engine.dispose()

    def read_data(self, tablename):
        self.mycursor.execute("SELECT * FROM {}".format(tablename))
        result = self.mycursor.fetchall()
        return result

    def update_data(self, input_field, new_data, old_data):
        sql = "UPDATE senvalues SET {} = '{}' WHERE {} = '{}'".format(input_field, new_data, input_field, old_data)
        self.mycursor.execute(sql)
        self.mydb.commit()

    def insert_new_fish_data(self, tagID, species, gender, cageNo, length):
        sql = "INSERT INTO fishdata (tagID, species, gender, cageNo, length) VALUES (%s, %s, %s, %s, %s)"
        val = (tagID, species, gender, cageNo, length)
        self.mycursor.execute(sql, val)

        self.mydb.commit()

    def delete_table(self, tablename):
        sql = "DROP TABLE {}".format(tablename)
        self.mycursor.execute(sql)


if __name__ == '__main__':
    database = database()

    print("Choose the following option:\n\n"
          "1. Create database\n"
          "2. Create sensor table\n"
          "3. Create fish table\n"
          "4. Delete table\n")

    user_input = input("Enter your number: ")
    if user_input == "1":
        database.create_database()
        print("Database was created succesfully")

    elif (user_input == "2"):
        database.create_sensor_table()
        print("Sensor table was created succesfully")

    elif (user_input == "3"):
        database.create_fish_table()
        print("Fish table was created succesfully")

    elif (user_input == "4"):
        tablename = input("Enter your table name: ")
        database.delete_table(tablename)
        print("Table {} deleted succesfully".format(tablename))