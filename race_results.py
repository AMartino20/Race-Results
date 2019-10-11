import cv2
import numpy as np
import pytesseract
import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


class User:
    """Driver info and maybe stats eventually"""

    standard_points = (20, 16, 14, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)
    d2_points = (50, 46, 44, 42, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31)
    d1_points = (80, 76, 74, 7, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61)

    def __init__(self, Driver, Name, Number, Nation, Affiliation, Manufacturer, **kwargs):
        self.driver = Driver
        self.name = Name
        self.number = Number
        self.nation = Nation
        self.affiliation = Affiliation
        self.manufacturer = Manufacturer
        self.kwargs = kwargs
        # results data format
        self.results = {}
        self.total_points = ''
        # might not need a points variable? Maybe it should be a list if I do need it?
        # self.points = []
        # run functions below here
        self.format_rounds()
        self.format_points()

        # print(self.driver)
        # print(self.results)

    def format_rounds(self):
        # Checks for the word Round, formats data around round entries
        # Then checks round value for * and +
        # If it sees * it creates dict entry for sub: True
        # If it sees + it creates dict entry for pole: True
        r = 1
        for k, v in self.kwargs.items():
            if 'Round' in k or 'round' in k:
                if not v:
                    pass
                else:
                    rn = f"round {r}"
                    self.results[rn] = {}
                    # Pole and sub are here just to prevent errors pending discovery of better way
                    # self.results[rn]['pole'] = False
                    # self.results[rn]['sub'] = False
                    # remove above this line if better way found
                    # a better way was found but leaving this in for possibility
                    # that I might want all data in all rounds

                    if '*' in v:
                        self.results[rn]['sub'] = True
                        v = v.replace('*', '')

                    if '+' in v:
                        self.results[rn]['pole'] = True
                        v = v.replace('+', '')

                    self.results[rn]['position'] = v
                    # print(k, v)
                    r = r + 1

        # might add code that removes empty dict values? might add unknown consequences later on

        # The code below removes strings and keeps its probably better used somewhere else
        # self.results = [int(x) for x in self.results if x.isdigit()]
        # this removes only empty strings, leaves list as all strings
        # self.results = [i for i in self.results if i]

    def format_points(self):
        t = 0
        for k, v in self.results.items():
            # needs isdigit to prevent error with DNX
            if v['position'].isdigit():
                round_pos = v['position']
                round_pos = int(round_pos) - 1
                pntval = User.standard_points[round_pos]
                if 'pole' in v.keys():
                    if v['pole']:
                        pntval = pntval + 1
                t = t + pntval
                v['points'] = pntval
        self.total_points = t


    # def sum_points(self):
    #     p = 0
    #     for k, v in self.results.items():
    #         p = p + int(v['points'])
    #     return p

    def manuregion(self):
        # Regions must be in lowercase
        asia_region = ('honda', 'hyundai', 'lexus', 'mazda', 'nissan', 'toyota')
        atlantic_region = ('aston martin', 'chevrolet', 'dodge', 'ford', 'jaguar')
        europe_region = ('audi', 'bmw', 'ferrari', 'lamborghini', 'mclaren', 'porsche', 'renault')

        # searches each region list and returns string of the region.
        if self.manufacturer.lower() in asia_region:
            return 'Asia'

        elif self.manufacturer.lower() in atlantic_region:
            return 'Atlantic'

        elif self.manufacturer.lower() in europe_region:
            return 'Europe'

        else:
            return 'Error'

    def print_info(self):
        print(f"{self.driver}'s driver information:")
        print(f"Username: {self.driver}")
        if self.name != '':
            print(f"Name: {self.name}")
        print(f"Nation: {self.nation}")
        print(f"Affiliation: {self.affiliation}")
        print(f"Manufacturer: {self.manufacturer}")
        print(f"Manufacturer Region: {self.manuregion()}")
        print('\n')


def import_csv(filename):
    # Import csv and create classes.
    # This resets the list of drivers
    users = []

    with open('RR_Sample.csv') as csvfile:
        readCSV = csv.DictReader(csvfile, delimiter=',')
        for row in readCSV:
            users.append(User(**row))

    return users


def dr_num(search):
    # searches driver list by number
    for x in driver_objects:
        if str(search) in x.number:
            return x


def dr_driver(search):
    # searches driver list by name
    for x in driver_objects:
        if str(search.lower()) in x.driver.lower():
            return x


def list_drivers(lower=False, pr=''):
    # putting p as the arg prints a list line by line, otherwise returns list
    for d in driver_objects:
        if pr == 'p':
            print(d.driver)
    dl = []
    for d in driver_objects:
        if lower:
            dl.append(d.driver.lower())
        else:
            dl.append(d.driver)
    if pr != 'p':
        return dl


# Image Processing Functions


def image_processing(full_image, y1, y2, x1, x2, t):
    # Image ROI
    roi = full_image[y1:y2, x1:x2]
    # Image processing
    ocr_image = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # pixel = int(ocr_image[4, 4])
    _, ocr_binary = cv2.threshold(ocr_image, t, 255, cv2.THRESH_BINARY_INV)

    return ocr_binary


def ocr_text(ocr_binary):
    ocr_string = pytesseract.image_to_string(ocr_binary, lang='eng', config="--psm 7")
    return ocr_string


def ocr_time():
    pass


def process_race_results(ss):
    data = {}
    row_y1 = 195
    row_y2 = 230
    # t is the threshold for the binary conversion of image processing
    t = 135
    # uses 14 because that is all that can show on race results screen
    for r in range(14):
        # for this function, ROI is only driver name
        d = image_processing(ss, row_y1, row_y2, 372, 700, t)
        d = ocr_text(d)
        # creates dictionary entry with row number as postion
        # there's no need to OCR position because it is a known factor
        data[r + 1] = d
        # moves row variables to next line
        row_y1 = row_y1 + 51
        row_y2 = row_y2 + 51

    # Use to see if theres a problem from this function
    # for r in data.values():
    #     print(r)
    # # cv2.imshow('Race Results', binary)
    return data


# Data Tools


def match_users(data):
    def print_fuzz():
        # clean_data list format: 1: Fuzzy match, fuzzy %, ocr, '' (substitute if applicable)
        # print(clean_data)
        print("\nPos | Match | Match % | Raw OCR | Substitute")
        for r in clean_data:
            match = clean_data[r][0]
            fuzzpercent = clean_data[r][1]
            ocr = clean_data[r][2]
            if clean_data[r][3] == False:
                sub = ''
            else:
                sub = clean_data[r][3]
            print(f"{r}: {match} | {fuzzpercent} | {ocr} | {sub}")

    # creates lowercase list of drivers for data comparison
    driverlist = list_drivers()
    driverlistlower = [item.lower() for item in driverlist]
    # creates empty list for the data from the ocr
    cleaned_dl = {}

    # Removes empty strings from function arg. I believe this is ok because the key is position
    clean_data = {k: v for k, v in data.items() if v is not ''}

    # this is the code that matches data. It replaces the key containing position with matched data
    # position (dict key): Fuzzy Match, Fuzzy %, ocr, empty string by default. This is replaced by sub name
    for p in clean_data:
        # Takes best match and defines as x
        x = list(process.extractOne(clean_data[p].lower(), driverlistlower))
        # matches best match with looped dict
        d = clean_data[p]
        # if match percent is greater than 50% input match, otherwise give **unknown** driver name
        if x[1] >= 50:
            clean_data[p] = [dr_driver(x[0]).driver, x[1], d, False]
        else:
            clean_data[p] = ['**Unknown**', x[1], d, False]

        # add .driver at end to get string of name, otherwise it's the object
        # and we need the object for the next steps
        cleaned_dl[p] = dr_driver(x[0])

    print_fuzz()

    # Enter substitute drivers
    # while loops allow for repeating the question if there is an error. breaks at
    while True:
        s = input('\nAre there any substitutes in this lobby? '
                  '\nEnter "y" or "n": ')
        while s == 'y':
            i = input('\nWhich position requires a driver swap? Type "exit" to go back.\n')
            # if else either keeps you in the loop or exits the loop
            if i == 'exit':
                break
            elif not i.isdigit() or i == '0':
                print('\nError: Please enter the position of the substitute.')
            # this is the code that does the work of swapping
            else:
                # if input is a number and NOT zero the following code works
                while i.isdigit() and i != '0':
                    d = input(f"\nWho did {clean_data[int(i)][2]} fill in for?"
                              '\nMAKE SURE YOU SPELL IT RIGHT! Capitalization does not matter.Type "exit" to go back.\n')
                    entry_list = list_drivers(lower=True)
                    # print(entry_list)
                    # checks spelling against entry list then rewrite list for that position
                    if d == 'exit':
                        break
                    elif d not in entry_list:
                        print("\nError: Please enter valid driver name. Type exit to go back.")
                    else:
                        print(f"\n{clean_data[int(i)][2]} filled in for {dr_driver(d).driver}")
                        clean_data[int(i)][0] = dr_driver(d).driver
                        clean_data[int(i)][3] = clean_data[int(i)][2]
                        print_fuzz()
                        break
                # this breaks out to asking if there are any substitutes.
                # This works because it only happens if it meets the else condition above
                break
        if s == 'n':
            break

    # Check For Errors
    #
    while True:
        i = input('\nIf there are any errors please enter position number. '
                  '\nEnter "finish" if everything is correct:\n')

        if i == 'finish' or i == 'Finish':
            break
        elif not i.isdigit() or i == '0':
            print('Error: Please enter valid position number\n')
        # elif i.isdigit() and i != '0':
        else:
            while True:
                entry_list = list_drivers(lower=True)
                d = input(f'\nWho finished in {i}? Type "exit" to go back'
                          "\nMAKE SURE YOU SPELL IT RIGHT! Capitalization does not matter.\n")
                if d == 'exit':
                    break
                elif d not in entry_list:
                    print("\nError: Please enter valid driver name. Type exit to cancel.")
                else:
                    clean_data[int(i)][0] = dr_driver(d).driver
                    print_fuzz()
                    break

    # print(cleaned_dl)

    # goes driver by driver from OCR and adds an entry to the results list
    # for p in cleaned_dl:
    #     d = cleaned_dl[p]
    #     d.results.append(p)
    #     print(d.driver, d.results)
    print(clean_data)
    return clean_data


def finalize_data(data):
    pass


# this defines the users list and image
driver_objects = import_csv('RR_Sample.csv')

img = cv2.imread('race_result_ss.png')
# match_users(process_race_results(img))

# dr_num('003').get_points()

print(dr_num('003').driver)
for r, v in dr_num('003').results.items():
    print(r)
    print(v)

print(f"Total Points: {dr_num('003').total_points}")
# print(dr_num(888).results)
# dr_driver('w1holesale').print_info()
