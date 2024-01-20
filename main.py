import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QTableWidgetItem, QMessageBox
from PyQt5.uic import loadUi
from PyQt5 import QtCore
import pandas as pd
import numpy as np
from datetime import datetime
import random
import pytz
from axis_interval import DateAxisItem
import BlynkLib
import pyqtgraph as pg
from mysql_init import database
from sqlalchemy import create_engine

class FishDetailsWidget(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('page2.ui', self)  # Assuming page2.ui is your UI file
        self.engine = create_engine(f'mysql+mysqlconnector://root:123456@localhost/mydatabase')
        self.database = database()
        self.fish_data = self.database.read_data("fishdata")
        self.columns = ['Primary key', 'TagID', 'Species', 'Gender', 'CageNo', 'Length']

        # Initialise button event
        self.button_update.clicked.connect(self.update_data)
        self.button_add.clicked.connect(self.add_data)
        self.button_delete.clicked.connect(self.delete_data)
        self.button_return.clicked.connect(self.go_to_page1)

        # Initialise total fishes
        self.initialise_data()

    def initialise_data(self):
        # Initialise fishes data

        self.df = pd.DataFrame(self.fish_data, columns=self.columns)
        print(self.df)
        # Initialise total fishes
        self.total_amount = len(self.df)
        self.gender_counts = self.df['Gender'].value_counts()
        self.male_count = self.gender_counts.get('Male', 0)
        self.female_count = self.total_amount - self.male_count
        self.length_greater_than_20_count = len(self.df[self.df['Length'] > 20])

        self.total_fishes.setText(str(self.total_amount))
        self.male_fishes.setText(str(self.male_count))
        self.female_fishes.setText(str(self.female_count))
        self.less20_fishes.setText(str(self.length_greater_than_20_count))

        # Table contents
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)

        # Populate the table with the Excel data
        self.table_widget.setRowCount(self.df.shape[0])
        self.table_widget.setColumnCount(self.df.shape[1])
        self.table_widget.setHorizontalHeaderLabels(self.df.columns)

        for row in range(self.df.shape[0]):
            for col in range(self.df.shape[1]):
                item = QTableWidgetItem(str(self.df.iloc[row, col]))
                self.table_widget.setItem(row, col, item)

    def update_data(self):
        pass

    def add_data(self):
        # Data to append (replace this with your actual data)
        self.database.insert_new_fish_data(self.id.text(), self.species_dropdown.currentText(),
                                           self.gender_dropdown.currentText(),
                                           self.cage_dropdown.currentText(), self.input_length.text())

        # Display popup
        self.show_popup()

        self.initialise_data()

    def delete_data(self):
        pass

    def show_popup(self):
        # Create a QMessageBox
        popup = QMessageBox(self)
        popup.setWindowTitle('Info')
        popup.setText('Data manipulation successful.')
        popup.setIcon(QMessageBox.Information)
        popup.addButton(QMessageBox.Ok)

        # Show the pop-up and wait for a button click
        popup.show()

    def go_to_page1(self):
        window.stacked_widget.setCurrentIndex(0)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        loadUi('main.ui', self)  # Replace 'your_ui_file.ui' with your actual UI file

        # Initialize database
        self.database = database()

        # Blynk credential
        self.BLYNK_AUTH_TOKEN = "P-4k0Ecv3BhsdGmAfZnAjriw199ATJD8"
        self.BLYNK_SERVER = "http://blynk-cloud.com"
        self.MOTOR_RIGHT = "V3"
        self.MOTOR_LEFT = "V4"
        self.blynk = BlynkLib.Blynk(self.BLYNK_AUTH_TOKEN)
        
        self.config = "config.txt"
        self.point_per_second = 1
        self.num_point = 30
        self.directory_path = "daily_data"
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.csv_filename = "{}.csv".format(self.current_date)

        # Switch to second page
        self.data_button.clicked.connect(self.page2_button)

        # Update config.txt
        self.confirm_button.clicked.connect(self.update_config)

        # Step 1: Read config.txt
        self.water_level, self.temp_value, self.ph_value = self.read_config()

        # Step 2: Setup graph
        self.setup_graph_widget()

        # Step 3: Initialise dataframe
        self.df = self.initial_dataframe()

        # Step 4: Plot the graph
        self.plot_data()

        # Step 5: Update plot
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.point_per_second * 1000)  # .setInterval in milisecond
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def initial_dataframe(self):
        timestamp_list = []

        # Check if the current time is later than the last timestamp in the data
        for i in range(self.num_point):
            kl_timezone = pytz.timezone('Asia/Kuala_Lumpur')
            initial_timestamp = datetime.now(kl_timezone).timestamp()
            new_timestamp = initial_timestamp + (i * self.point_per_second)
            timestamp_list.append(new_timestamp)

        data = {
            'Timestamp': timestamp_list,
            'WaterLevel': len(list(range(self.num_point))) * [0],
            'TempValue': len(list(range(self.num_point))) * [0],
            'phValue': len(list(range(self.num_point))) * [0]
        }

        df = pd.DataFrame(data)
        return df

    def append_to_dataframe(self, current_df, timestamp, water_level, temp_value, ph_value):
        new_data = {
            "Timestamp": timestamp,
            "WaterLevel": water_level,
            "TempValue": temp_value,
            "phValue": ph_value
        }

        updated_df = current_df.append(new_data, ignore_index=True)
        return updated_df

    def save_csv(self, file_path, new_dataframe):
        try:
            with open(file_path, 'a', newline='') as file:
                new_dataframe.to_csv(file, header=False, index=False)

        except FileNotFoundError as e:
            print(e)

    def setup_graph_widget(self):
        self.tempGraph.setMouseEnabled(x=True, y=False)  # Enable horizontal panning
        self.tempGraph.setMenuEnabled(False)
        self.phGraph.setMouseEnabled(x=True, y=False)
        self.phGraph.setMenuEnabled(False)
        self.waterGraph.setMouseEnabled(x=True, y=False)
        self.waterGraph.setMenuEnabled(False)

        axis1 = DateAxisItem(orientation='bottom')
        axis2 = DateAxisItem(orientation='bottom')
        axis3 = DateAxisItem(orientation='bottom')
        axis1.attachToPlotItem(self.tempGraph.getPlotItem())
        axis2.attachToPlotItem(self.phGraph.getPlotItem())
        axis3.attachToPlotItem(self.waterGraph.getPlotItem())

        self.input_water.setText("{}".format(self.water_level))
        self.input_temp.setText("{}".format(self.temp_value))
        self.input_ph.setText("{}".format(self.ph_value))
        self.slider_left.setRange(0, 100)
        self.slider_right.setRange(0, 100)

        self.water_limit = pg.InfiniteLine(pos=self.water_level, angle=0, pen=pg.mkPen(color='r', width=1))
        self.temp_limit = pg.InfiniteLine(pos=self.temp_value, angle=0, pen=pg.mkPen(color='r', width=1))
        self.ph_limit = pg.InfiniteLine(pos=self.ph_value, angle=0, pen=pg.mkPen(color='r', width=1))
        self.waterGraph.addItem(self.water_limit)
        self.tempGraph.addItem(self.temp_limit)
        self.phGraph.addItem(self.ph_limit)

        self.waterGraph.setBackground('w')
        self.tempGraph.setBackground('w')
        self.phGraph.setBackground('w')

    def plot_data(self):
        start_time_second = self.df["Timestamp"].values[0]
        end_time_second = self.df["Timestamp"].values[-1]
        timestamps = np.linspace(start_time_second, end_time_second,len(self.df["Timestamp"].values))

        # Plot the line graph with red color for the area under the curve
        pen_sens1 = pg.mkPen(color=(0, 0, 0), width=1, cosmetic=True)
        pen_sens2 = pg.mkPen(color=(0, 0, 0), width=1, cosmetic=True)
        pen_sens3 = pg.mkPen(color=(0, 0, 0), width=1, cosmetic=True)

        self.sen1_line = self.tempGraph.plot(timestamps, self.df["WaterLevel"], pen=pen_sens1, name="WaterLevel")
        self.sen2_line = self.phGraph.plot(timestamps, self.df["TempValue"], pen=pen_sens2, name="TempValue")
        self.sen3_line = self.waterGraph.plot(timestamps, self.df["phValue"], pen=pen_sens3, name="phValue")

    def read_sensor_value(self):
        water_level_value = random.uniform(0, 20)
        temp_value = random.uniform(20, 50)
        ph_value = random.uniform(1, 14)
        
        adc = 1024
        water_level_max = 100
        temperature_max = 100
        ph_max = 14
        
        cal_water = (water_level_value / adc) * water_level_max
        cal_temp = (temp_value / adc) * temperature_max
        cal_ph = (ph_value / adc) * ph_max
        
        # Update blynk values
        self.blynk.virtual_write(0, cal_temp)
        self.blynk.virtual_write(1, cal_water)
        self.blynk.virtual_write(2, cal_ph)

        list_values = [water_level_value, temp_value, ph_value]
        cal_list_values = []

        for value in list_values:

            cal_list_values.append(value)

        return cal_list_values

    def update_plot_data(self):
        # Read sensor value from MCP3008
        sensor_values = self.read_sensor_value()

        self.blynk.run()

        new_date = self.df["Timestamp"].iloc[-1] + self.point_per_second
        if self.num_point == 0:
            self.database.insert_multi_data(self.df)
            self.num_point = 30
            #self.save_csv(self.file_path, self.df)
        else:
            self.num_point -= 1

        # Append the new sensors data to the dataframe
        self.df = self.append_to_dataframe(self.df,
                                           new_date,
                                           sensor_values[0],
                                           sensor_values[1],
                                           sensor_values[2])

        # Drop the 1st row from dataframe
        self.df.drop(index=self.df.index[0], inplace=True)

        self.sen1_line.setData(self.df["Timestamp"].values, self.df["WaterLevel"].values)
        self.sen2_line.setData(self.df["Timestamp"].values, self.df["TempValue"].values)
        self.sen3_line.setData(self.df["Timestamp"].values, self.df["phValue"].values)

    def update_config(self):
        water_level = self.input_water.text()
        temp_value = self.input_temp.text()
        ph_value = self.input_temp.text()

        new_water_level = round(float(water_level), 1)
        new_temp = round(float(temp_value), 1)
        new_ph = round(float(ph_value), 1)

        # Read the existing content and parse variable values
        with open(self.config, "r") as file:
            lines = file.readlines()

        updated_lines = []
        for line in lines:
            if line.startswith("water_level"):
                updated_lines.append("water_level = {}\n".format(new_water_level))
            elif line.startswith("Temperature_value"):
                updated_lines.append("Temperature_value = {}\n".format(new_temp))
            elif line.startswith("ph_value"):
                updated_lines.append("ph_value = {}\n".format(new_ph))
            else:
                updated_lines.append(line)

        # Write the modified content back to the file
        with open(self.config, "w") as file:
            file.writelines(updated_lines)

        print("Variable values have been updated.")

        QtCore.QCoreApplication.quit()
        status = QtCore.QProcess.startDetached(sys.executable, sys.argv)

        return new_water_level, new_temp, new_ph

    def read_config(self):
        water_level = None
        temp_value = None
        ph_value = None

        # Read and parse the variable values
        with open(self.config, "r") as file:
            lines = file.readlines()

        for line in lines:
            if line.startswith("water_level"):
                water_level = float(line.split("=")[1].strip())
            elif line.startswith("Temperature_value"):
                temp_value = float(line.split("=")[1].strip())
            elif line.startswith("ph_value"):
                ph_value = float(line.split("=")[1].strip())

        return water_level, temp_value, ph_value

    def page2_button(self):
        self.file_path = "C:/Users/llx/Desktop/Sem 7/SEEE4723-02 CAPSTONE PROJECT/Development/daily_data/fish_data.csv"
        # Second page initialization
        central_widget = FishDetailsWidget()
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.addWidget(central_widget)
        self.setCentralWidget(self.stacked_widget)

        self.stacked_widget.setCurrentIndex(0)
        self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
