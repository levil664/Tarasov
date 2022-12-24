import csv
import re
import math
import os


class InputCorrect:
    def __init__(self, file: str):
        self.in_file_name = file
        self.check_file()

    def check_file(self):
        with open(self.in_file_name, "r", encoding='utf-8-sig', newline='') as csv_file:
            file_iter = iter(csv.reader(csv_file))
            if next(file_iter, "none") == "none": do_exit("Пустой файл")
            if next(file_iter, "none") == "none": do_exit("Нет данных")

def divide_csv_file(csv_dir: str):
    input_data = InputCorrect(input("Введите название файла: "))
    if not os.path.exists(csv_dir):
        os.mkdir(csv_dir)
    data_set = DataSet(input_data, csv_dir)


class DataSet:
    def __init__(self, input_data: InputCorrect, csv_dir: str):
        self.input_values = input_data
        self.dir = csv_dir
        self.csv_reader()
        self.split_csv()

    def csv_reader(self):
        with open(self.input_values.in_file_name, "r", encoding='utf-8-sig', newline='') as csv_file:
            file = csv.reader(csv_file)
            self.start_line = next(file)
            self.other_lines = [line for line in file
                                if not ("" in line) and len(line) == len(self.start_line)]
            self.year_index = self.start_line.index("published_at")

    @staticmethod
    def get_year_method_3(data: str):
        return data[:4]

    def save_file(self, current_year: str, lines: list):
        with open(f"{self.dir}/file_{current_year}.csv", "a", encoding='utf-8-sig', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(lines)

    def split_csv(self):
        current_year = DataSet.get_year_method_3(self.other_lines[0][self.year_index])
        index = 0
        years_matrix = [[]]
        for line in self.other_lines:
            line_year = DataSet.get_year_method_3(line[self.year_index])
            if line_year != current_year:
                self.save_file(current_year, years_matrix[index])
                current_year = line_year
                index += 1
                years_matrix.append([])
            years_matrix[index].append(line)
        self.save_file(current_year, years_matrix[index])


def do_exit(message):
    print(message)
    exit(0)


if __name__ == '__main__':
   divide_csv_file("csv")