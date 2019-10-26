import cv2
import pytesseract
import csv
from fuzzywuzzy import process
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os
import pycountry
from PIL import ImageTk, Image
import pickle


class User:
    """Driver info and maybe stats eventually"""

    standard_points = (20, 16, 14, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1)
    d2_points = (50, 46, 44, 42, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31)
    d1_points = (80, 76, 74, 7, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61)

    gt3_manu = ('Chevrolet', 'Dodge', 'Ford', 'Honda', 'Mazda', 'Mitsubishi',
                'Nissan', 'Subaru', 'Toyota', 'Lexus', 'Hyundai', 'Aston Martin',
                'Jaguar', 'Mclaren', 'Audi', 'BMW', 'Mercedes-Benz', 'Volkswagen',
                'Porsche', 'Citroen', 'Peugeot', 'Renault Sport', 'Alfa Romeo',
                'Ferrari', 'Lamborghini')

    def __init__(self, Driver, Name, Number, Nation, Affiliation, Manufacturer, **kwargs):
        self.driver = Driver
        self.name = Name
        self.number = str(Number.replace('#', ''))
        self.nation = Nation
        self.affiliation = Affiliation
        self.manufacturer = Manufacturer
        self.active = True
        self.kwargs = kwargs
        # results data formatting
        self.raw_results = {}
        self.results = {}
        self.total_points = ''  # This is defined at end of format_points()
        # might not need a points variable? Maybe it should be a list if I do need it?
        # self.points = []
        # run functions below here
        self.format_rounds()
        self.format_points()

    def format_rounds(self):
        # Checks for the word Round, formats data around round entries
        for k, v in self.kwargs.items():
            # Creates round entries in self.raw_results from self.kwargs
            if 'Round' in k or 'round' in k:
                if not v:
                    pass
                else:
                    rn = k.lower()
                    self.raw_results[k] = v
        for k, v in self.raw_results.items():
            self.process_points_string(k, v)

    def format_points(self):
        # adds self.results key for points using class tuples. Might have to rework this
        # if I add support for multiple series
        t = 0
        for k, v in self.results.items():
            # needs isdigit to prevent error with DNX
            if v['position'].isdigit():
                round_pos = v['position']
                round_pos = int(round_pos) - 1
                pntval = User.standard_points[round_pos]
                if 'pole' in v.keys() and v['pole']:
                    pntval = pntval + 1
                t = t + pntval
                v['points'] = pntval
        self.total_points = t

    def process_points_string(self, k, v):
        # Checks string v for * and +
        # If it sees * it creates dict entry for sub: True
        # If it sees + it creates dict entry for pole: True
        rn = k.lower()
        self.results[rn] = {}

        if '*' in v:
            self.results[rn]['absent'] = True
            v = v.replace('*', '')

        if '+' in v:
            self.results[rn]['pole'] = True
            v = v.replace('+', '')

        self.results[rn]['position'] = v

    def sum_points(self):
        pass
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
        print(f"Number: #{self.number}")
        print(f"Nation: {self.nation}")
        if self.affiliation != '':
            print(f"Affiliation: {self.affiliation}")
        print(f"Manufacturer: {self.manufacturer}")
        print(f"Manufacturer Region: {self.manuregion()}")
        print('\n')


class Round:
    pass


def import_csv(filename):
    # Import csv and create classes.

    print("Importing New CSV")
    # This resets the list of drivers
    users = []

    with open(filename) as csvfile:
        readCSV = csv.DictReader(csvfile, delimiter=',')
        for row in readCSV:
            users.append(User(**row))

    return users


# cli
def import_round(filename):
    # 2 columns, driver name and position, no header
    print('Importing Round CSV')

    while True:
        r = input("Input Round Number:\n")
        if r.isdigit():
            r = f"round {r}"
            break
        else:
            print("Please Enter Number Only")

    with open(filename) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        missing_drivers = []
        for row in readCSV:
            # searches for driver name, if it finds one, appropriate dict entry
            if dr_driver(row[0]) is not None:
                # dr_driver(row[0]).results[f"round {r}"] = row[1]
                d = dr_driver(row[0])
                d.raw_results[r] = row[1]
                d.process_points_string(r, row[1])

                print(d.driver)
                print(d.raw_results)
                print(d.results)

            # adds nested row list to missing drivers in order to run build_driver
            # or make a substitution
            elif dr_driver(row[0]) is None:
                missing_drivers.append(row)

        for md in missing_drivers:
            while True:
                i = input(f"\nIs {md[0]} a new driver or a substitute?\n"
                          "Options:\n"
                          "Enter 'new' to build driver entry\n"
                          f"Enter 'sub' if {md[0]} is a substitute\n"
                          "Enter 'skip' to skip driver. **WARNING: CANNOT UNDO**\n")
                if i == 'skip':
                    break
                elif i == 'new':
                    build_driver(driverentry=md[0])
                    d = dr_driver(md[0])
                    d.raw_results[r] = md[1]
                    d.process_points_string(r, md[1])
                    break
                elif i == 'sub':
                    while True:
                        s = input(f"Who did {md[0]} substitute for?\n")
                        if dr_driver(s) is not None:
                            d = dr_driver(s)
                            d.raw_results[r] = md[1]
                            d.process_points_string(r, md[1])
                            print(f"{md[0]} drove for {d.driver}")
                            break
                        else:
                            print("Driver Not Found")
                    break


# cli
def build_driver(driverentry=False):
    # build a driver object from user input

    def name_input():
        while True:
            name = input(f"Enter {driver}'s real name. Enter 'skip' to leave blank.\n")
            if name == 'skip':
                name = None
                break
            else:
                break
        return name

    def num_input():
        while True:
            number = str(input(f"Enter {driver}'s number.\n"))
            # check if someone already has this number
            in_use = False
            for d in driver_objects:
                if number == d.number:
                    in_use = True
                    print(f"Error: Number already in use by {d.driver}")
            if not in_use:
                break
            else:
                print("Invalid Entry")

        return number

    def nation_input():
        while True:
            nation = input("Enter 3 digit country code\n")
            if nation.isalpha() and len(nation) == 3:
                break
            else:
                print("Invalid Entry")
        return nation.upper()

    def affiliaton_input():
        while True:
            i = input(f"Enter {driver}'s team or affiliation.\n"
                      "Note: Capitalization **DOES** matter.\n"
                      "Enter 'skip' for no team or affiliation.\n")
            if i == 'skip':
                i = None
                break
        affiliation = i
        return affiliation

    def manu_input():
        while True:
            manufacturer = input(f"Enter {driver}'s manufacturer.\n")
            manu_list = [item.lower() for item in User.gt3_manu]
            # checks for entry in lowercase list then replaces with correct capitalization
            if manufacturer.lower() in manu_list:
                for manu in User.gt3_manu:
                    if manu.lower() == manufacturer:
                        manufacturer = manu
                break
            else:
                print("Invalid Entry")
        return manufacturer

    def verify_driver():
        pass

    print("Adding new driver to database")
    # Driver, Name, Number, Nation, Affiliation, Manufacturer

    # Driver PSN
    while True:
        if driverentry is not False:
            driver = driverentry
            driverentry = False
        else:
            driver = input("\nPlease enter driver PSN\n"
                           "Note: Capitalization **DOES** matter.\n")
        # PSN can't have a space in it
        if ' ' in driver:
            print("PSN cannot contain spaces\n")
            continue
        # PSN can't be less than 3 characters (might want to check actual rules for psn name
        elif len(driver) <= 3:
            print("Invalid Entry")
            continue
        else:
            while True:
                check = input(f"Begin building entry for {driver}? Enter 'n' to restart, 'y' to continue\n")
                if check == 'n':
                    break
                elif check == 'y':
                    break
                else:
                    print("Invalid Entry")
                    continue
        if check == 'y':
            check = None
            break

    name = name_input()
    number = num_input()
    nation = nation_input()
    affiliation = affiliaton_input()
    manufacturer = manu_input()

    # Verify Data
    verify_driver()

    while True:
        print(f"\nDriver: {driver}\n"
              f"1. Name: {name}\n"
              f"2. Number: #{number}\n"
              f"3. Nation: {nation}\n"
              f"4. Affiliation: {affiliation}\n"
              f"5. Manufacturer: {manufacturer}\n")
        modify = input("Is everything correct? Enter 'y' or 'n'.\n")
        if modify == 'y':
            break
        elif modify == 'n':
            change = input("Enter line number you wish to change.\n")
            if change == '1':
                name = name_input()
            elif change == '2':
                number = num_input()
            elif change == '3':
                nation = nation_input()
            elif change == '4':
                affiliation = affiliaton_input()
            elif change == '5':
                manufacturer = manu_input()
            else:
                print('Invalid Entry')
        else:
            print("Invalid Entry")

    add_driver = User(driver, name, number, nation, affiliation, manufacturer)

    driver_objects.append(add_driver)
    print("User added to database")


def dr_num(search):
    # searches driver list by number
    for x in driver_objects:
        if str(search) == x.number:
            return x


def dr_driver(search):
    # searches driver list by name
    for x in driver_objects:
        if str(search.lower()) == x.driver.lower():
            return x


def list_drivers(sort):
    if sort == "points":
        sortedlist = sorted(driver_objects, key=lambda x: x.total_points, reverse=True)
        return sortedlist
    elif sort == "psn":
        sortedlist = sorted(driver_objects, key=lambda x: x.driver.lower())
        return sortedlist
    elif sort == "num":
        sortedlist = sorted(driver_objects, key=lambda x: x.number)
        return sortedlist
    else:
        return driver_objects

    # dl = []
    # for d in sortedlist:
    #     if lower:
    #         dl.append(d.driver.lower())
    #     else:
    #         dl.append(d.driver)
    # return dl


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

# cli
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


# cli
def finalize_data(data):
    pass


# GUI FUNCTIONS


def donothing():
    pass


def nodata():
    # What to show when no league data is loaded.
    # might add disable functions for menu bar here too?
    nodataframe = LabelFrame(root).pack()
    Label(nodataframe, text="Please open data or import new league.").pack(padx=20, pady=20)


def new_league():
    def finish():
        global csvlocation_league
        if not nameentry.get() or not seriesentry.get():
            messagebox.showerror("Empty Fields", "Name and Series required")

        elif csvlocation_league is None:
            messagebox.showerror("No CSV Selected", "Please choose a CSV file to import.")

        else:
            global league_info
            league_info["name"] = nameentry.get()
            league_info["series"] = seriesentry.get()
            league_info["shortname"] = nameshortentry.get()
            # league_info["logo"] = logofile
            league_info["csv"] = csvlocation_league
            csvlocation_league = None

            new_league_frame.grid_forget()
            new_league_frame.destroy()
            newleaguewindow.destroy()

            global league_name
            global series_name
            league_name.set(league_info.get("name"))
            series_name.set(league_info.get("series"))
            # global league_logo
            # # league_logo = ImageTk.PhotoImage(Image.open(logofile))
            # league_logo = Image.open(logofile)
            # league_logo = league_logo.resize((200,200), Image.ANTIALIAS)
            # league_logo = ImageTk.PhotoImage(league_logo)
            # logo_label.configure(image=league_logo)

            global driver_objects
            driver_objects = import_csv(league_info["csv"])
            # Sort by total number of points
            top_drivers = sorted(driver_objects, key=lambda x: x.total_points, reverse=True)

            top_drivers_main(top_drivers)
            menu_state()

    newleaguewindow = Toplevel()
    newleaguewindow.attributes('-topmost', 'true')

    new_league_frame = LabelFrame(newleaguewindow, text="Create New League")
    new_league_frame.pack(padx=10, pady=10)

    nameentry = Entry(new_league_frame)
    Label(new_league_frame, text="League Name").grid(row=0, column=0, sticky=W, pady=5, padx=5)
    nameentry.grid(row=0, column=1, columnspan=2, padx=5)

    nameshortentry = Entry(new_league_frame)
    Label(new_league_frame, text="Short Name*").grid(row=1, column=0, sticky=W, pady=5, padx=5)
    nameshortentry.grid(row=1, column=1, columnspan=2, padx=5)

    seriesentry = Entry(new_league_frame)
    Label(new_league_frame, text="Series Name").grid(row=2, column=0, sticky=W, pady=5, padx=5)
    seriesentry.grid(row=2, column=1, columnspan=2, padx=5)

    def choose_csv():
        global csvlocation_league
        csvlocation_league = filedialog.askopenfilename(initialdir="", title="Select Driver List CSV",
                                                        filetypes=[("CSV files", "*.csv")])

        if csvlocation_league:
            # Adds error checking information to window
            validcsv.configure(text="OK", fg="black")
            csvname = StringVar()
            csvname.set(os.path.basename(csvlocation_league))
            Label(new_league_frame, textvariable=csvname).grid(row=4, column=1, columnspan=2)

        else:
            csvlocation_league = None

    Label(new_league_frame, text="Driver List").grid(row=3, column=0, sticky=W, pady=5, padx=5)
    Button(new_league_frame, text="choose csv", command=choose_csv,
           ).grid(row=3, column=1, pady=5, padx=5)

    global validcsv
    validcsv = Label(new_league_frame, text="X", fg="red")
    validcsv.grid(row=3, column=2, pady=5, padx=5)

    def choose_logo():
        global logofile
        logofile = filedialog.askopenfilename(initialdir="", title="Select League Logo")

    # League logo stuff, need to work out resize and respect aspect rations, until then removing button
    # Label(new_league_frame, text="League Logo").grid(row=4, column=0, sticky=W, pady=5, padx=5)
    # Button(new_league_frame, text="choose image", command=choose_logo,
    #        ).grid(row=4, column=1, pady=5, padx=5)

    Button(new_league_frame, text="Start New League", command=finish).grid(row=5, column=0, columnspan=3, padx=15,
                                                                           pady=15)


def new_driver():
    edit_driver(newdriver=True)


def edit_driver(newdriver=False):
    def new():
        edit_driver_frame.configure(text="New Driver")

        psnentry.configure(state=NORMAL)
        editpsnlabel.configure(text="Driver PSN:")
        activebtn.select()

    def edit():
        choosedriver = OptionMenu(edit_driver_frame, selected, *driverlist)
        # when selected driver changes, run select psn
        selected.trace_variable('w', select_psn)

        Label(edit_driver_frame, text="Driver PSN:").grid(row=0, column=0, sticky=W, pady=5, padx=5)
        choosedriver.configure(width=entrywidth)
        choosedriver.grid(row=0, column=2, padx=5, sticky=E + W)

        Checkbutton(edit_driver_frame, variable=changepsn, command=check_new_psn).grid(row=1, column=0, sticky=E)

    def cancel():
        edit_driver_frame.grid_forget()
        edit_driver_frame.destroy()
        drivereditwindow.destroy()

    def save_driver():
        # This is only here to remove error of not undefined var
        driver = None

        if newdriver:
            driver = newpsn.get()

        elif not newdriver:
            # sets d as driver object using driver search
            d = dr_driver(selected.get())
            if d is None:
                messagebox.showerror("Error", "Error:\nNo Driver Selected")
                return

            # If selected driver doesn't match newpsn check if edit requested
            # probably should remove .lower() but don't want to break it!
            if selected.get().lower() != newpsn.get().lower():
                # Sets driver var by checking if checkbox is checked, if true use entry, if false use selected
                if changepsn.get() == 1:
                    r = messagebox.askokcancel("Edit Driver PSN?", "Click OK to change Driver PSN")
                    if r == 0:
                        return
                    if r == 1:
                        driver = newpsn.get()
            elif changepsn.get() == 0:
                driver = selected.get()

        if driver is not None:
            if len(driver) > 16:
                messagebox.showerror("Error", "Error:\nPSN must be less than 16 characters.")
                return
            elif len(driver) <= 3:
                messagebox.showerror("Error", "Error:\nPSN must be more than 3 characters.")
                return
            elif " " in driver:
                messagebox.showerror("Error", "Error:\nDriver PSN can not have spaces.")
                return

        # ZERO IDEA WHY THIS DIDN'T WORK. Leaving it in so I can ponder it later
        # if newpsn.get().lower() == [x.driver.lower() for x in driver_objects]:
        #     messagebox.showerror("Error", "Error:\nDriver PSN already in use.")
        #     return

        # checks to see if driver psn is already in use
        if selected.get().lower() != newpsn.get().lower():
            for x in driverlist:
                if newpsn.get().lower() == x:
                    messagebox.showerror("Error", "Error:\nDriver PSN already in use.")
                    return

        # Checks if numentry is empty, NOT if string is 0
        if len(numentry.get()) == 0:
            messagebox.showerror("Error", "Error:\nPlease enter driver number.")
            return

        # Checks for # sign, removes if found. redefines numentry as n
        n = numentry.get()
        n = n.replace("#", "")

        if len(n) == 0 or len(n) > 3:
            messagebox.showerror("Error", "Error:\nDriver Number must be between 1 and 3 numbers.")
            return

        # The idea for this is that if driver number matches driver, skip
        for x in driver_objects:
            if n == x.number and selected.get().lower() == x.driver.lower():
                pass
            elif n == x.number:
                messagebox.showerror("Error", f"Error:\nDriver Number already in use by {x.driver}.")
                return

        if len(nationentry.get()) != 3:
            messagebox.showerror("Error", "Error:\nPlease enter 3 digit driver nation.")
            return
        elif nationentry.get().upper() not in [country.alpha_3 for country in pycountry.countries]:
            messagebox.showerror("Error", "Error:\nPlease enter correct 3 digit country code.")
            return

        # finalize details
        if not newdriver:
            sd = dr_driver(selected.get())
            if sd is None:
                messagebox.showerror("Error", "Error:\nDid you select a driver?")
            elif sd:
                if changepsn.get() == 1:
                    sd.driver = newpsn.get()
                    # print(sd.driver)
                if nameentry.get() != sd.name:
                    sd.name = nameentry.get()
                    # print(sd.name)
                if n != sd.number:
                    sd.number = n
                    # print(sd.number)
                if nationentry.get() != sd.nation:
                    sd.nation = nationentry.get().upper()
                    # print(sd.nation)
                if affilentry != sd.affiliation:
                    sd.affiliation = affilentry.get()
                    # print(sd.affiliation)
                if selected_manu.get() != sd.manufacturer:
                    sd.manufacturer = selected_manu.get()
                    # print(sd.manufacturer)
                if activecheck == 0:
                    sd.active = False
                elif activecheck == 1:
                    sd.active = True
        elif newdriver:
            driver_objects.append(User(newpsn.get(), nameentry.get(), n, nationentry.get(),
                                       affilentry.get(), manuentry.get()))

        # print("Input Data")
        # print(f"{selected.get()}\n{newpsn.get()}\n{nameentry.get()}\n{n}\n"
        #       f"{nationentry.get().upper()}\n{affilentry.get()}\n{selected_manu.get()}")

        # print("Saved Data:")
        # print(f"{sd.driver}\n{sd.name}\n{n}\n"
        #       f"{sd.nation}\n{sd.affiliation}\n{sd.manufacturer}")

    drivereditwindow = Toplevel()
    # drivereditwindow.attributes('-topmost', 'true')
    drivereditwindow.resizable(False, False)

    edit_driver_frame = LabelFrame(drivereditwindow, text="Edit Driver")
    edit_driver_frame.pack(padx=10, pady=10)

    selected = StringVar()
    newpsn = StringVar()
    selected_manu = StringVar()
    selected.set("Select Driver")
    selected_manu.set("Select Manufacturer")
    sorted_drivers = list_drivers("psn")
    driverlist = [x.driver.lower() for x in sorted_drivers]

    def select_psn(*args):
        d = dr_driver(selected.get())
        if not d:
            pass
        else:
            newpsn.set(d.driver)

            nameentry.delete(0, END)
            nameentry.insert(0, d.name)

            nationentry.delete(0, END)
            nationentry.insert(0, d.nation)

            numentry.delete(0, END)
            numentry.insert(0, "#")
            numentry.insert(1, d.number)

            affilentry.delete(0, END)
            affilentry.insert(0, d.affiliation)

            selected_manu.set(d.manufacturer)

            if d.active:
                activebtn.select()
            else:
                activebtn.deselect()

    def check_new_psn():
        if changepsn.get() == 1:
            psnentry.configure(state=NORMAL)
        elif changepsn.get() == 0:
            # reset psnentry field before disable
            psnentry.delete(0, END)
            psnentry.insert(0, selected.get())
            psnentry.configure(state=DISABLED)

    entrywidth = 20
    changepsn = IntVar()

    psnentry = Entry(edit_driver_frame, state=DISABLED, textvariable=newpsn)
    editpsnlabel = Label(edit_driver_frame, text="Edit PSN:")
    editpsnlabel.grid(row=1, column=0, sticky=W, pady=5, padx=5)
    psnentry.grid(row=1, column=2, padx=5, sticky=E + W)

    nameentry = Entry(edit_driver_frame)
    Label(edit_driver_frame, text="Real Name:*").grid(row=2, column=0, sticky=W, pady=5, padx=5)
    nameentry.grid(row=2, column=2, padx=5, sticky=E + W)

    numentry = Entry(edit_driver_frame)
    Label(edit_driver_frame, text="Driver Number:").grid(row=3, column=0, sticky=W, pady=5, padx=5)
    numentry.grid(row=3, column=2, padx=5, sticky=E + W)

    nationentry = Entry(edit_driver_frame)
    Label(edit_driver_frame, text="Nation:").grid(row=4, column=0, sticky=W, pady=5, padx=5)
    nationentry.grid(row=4, column=2, padx=5, sticky=E + W)

    affilentry = Entry(edit_driver_frame)
    Label(edit_driver_frame, text="Affiliation:*").grid(row=6, column=0, sticky=W, pady=5, padx=5)
    affilentry.grid(row=6, column=2, padx=5, sticky=E + W)

    manuentry = OptionMenu(edit_driver_frame, selected_manu, *sorted(User.gt3_manu))
    Label(edit_driver_frame, text="Manufacturer:").grid(row=7, column=0, sticky=W, pady=5, padx=5)
    manuentry.grid(row=7, column=2, padx=5, sticky=E + W)

    activecheck = IntVar
    Label(edit_driver_frame, text="Active Driver").grid(row=8, column=0, sticky=W, pady=5, padx=5)
    activebtn = Checkbutton(edit_driver_frame, variable=activecheck)
    activebtn.grid(row=8, column=2)

    Button(edit_driver_frame, text="Cancel", command=cancel, padx=10).grid(row=9, column=0, padx=15, pady=15, sticky=W)
    Button(edit_driver_frame, text="Save Driver", command=save_driver, padx=10).grid(row=9, column=2, padx=15, pady=15,
                                                                                     sticky=E)

    # will use this to change options to allow new driver.
    # Should be simpler than two nearly identical windows
    if newdriver:
        new()
    if not newdriver:
        edit()


def results_viewer():
    def write_results():

        resultstree = ttk.Treeview(resultswindow, height=28)
        resultstree['show'] = 'headings'
        resultstree["columns"] = ("pos", "psn", "name", "number", "nation", "affil", "manu", "manuregion",
                                  "points", "active")
        resultstree.grid(row=1, column=0)
        resultstree.heading("#0", text="", anchor="w")
        resultstree.column("#0")

        resultstree.heading("pos", text="POS", anchor="e")
        resultstree.column("pos", anchor="e", width=40)

        resultstree.heading("psn", text="PSN", anchor="w")
        resultstree.column("psn", anchor="w", width=125)

        resultstree.heading("name", text="Name*", anchor="w")
        resultstree.column("name", anchor="w", width=100)

        resultstree.heading("number", text="#", anchor="w")
        resultstree.column("number", anchor="w", width=50)

        resultstree.heading("nation", text="Nation", anchor="w")
        resultstree.column("nation", anchor="w", width=50)

        resultstree.heading("affil", text="Affiliation*", anchor="w")
        resultstree.column("affil", anchor="w", width=175)

        resultstree.heading("manu", text="Manufacturer", anchor="w")
        resultstree.column("manu", anchor="w", width=100)

        resultstree.heading("manuregion", text="Region", anchor="w")
        resultstree.column("manuregion", anchor="w", width=70)

        resultstree.heading("points", text="Points", anchor="w")
        resultstree.column("points", anchor="w", width=50)

        resultstree.heading("active", text="Active", anchor="w")
        resultstree.column("active", anchor="w", width=50)

        i = 1
        for d in list_drivers(sort="points"):
            n = f"#{d.number}"
            if (i % 2) == 0:
                rowtag = "evenrow"
            else:
                rowtag = "oddrow"

            resultstree.insert('', 'end', str(i), values=(i, d.driver, d.name, n, d.nation, d.affiliation,
                                                          d.manufacturer, d.manuregion(), d.total_points, d.active),
                               tags=rowtag)
            # resultstree.item(str(i), tags=[str(rowtag)])
            i += 1

        # Bug is ttk makes this not work I think?
        resultstree.tag_configure("evenrow", background="#DFDFDF")

    resultswindow = Toplevel()
    resultswindow.title("Overall Results")
    resultsinfo = Frame(resultswindow, padx=10, pady=5)

    # scrollbar = Scrollbar(???)

    resultsinfo.grid(row=0, column=0, sticky=NSEW)
    Label(resultsinfo, textvariable=league_name, font=("", 18)).grid(row=0, column=0, padx=5, pady=5, sticky=W)
    Label(resultsinfo, textvariable=series_name, font=("", 14)).grid(row=1, column=0, padx=5, pady=5, sticky=W)

    write_results()


def import_screenshot():
    # import_screenshot = Toplevel()
    pass

driver_objects = []
csvlocation_league = None
league_info = {"name": "League Name", "series": "Series Name"}

# creates the base level window
root = Tk()
root.title("League Manager - Alpha 0.1")


# root.geometry('400x500')


def test_league():
    global driver_objects
    driver_objects = import_csv('RR_Sample.csv')
    global league_info
    league_info = {"name": "eSports Global Tournament", "shortname": "eSGT", "series": "GT3 Series"}


test_league()

league_name = StringVar()
league_name.set(league_info.get("name"))
series_name = StringVar()
series_name.set(league_info.get("series"))

# Menu Bar
menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="New League", command=new_league)
filemenu.add_command(label="Open", command=donothing)
filemenu.add_command(label="Save", command=donothing)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

importmenu = Menu(menubar, tearoff=0)
importmenu.add_command(label="Import Round Settings", command=donothing)
importmenu.add_separator()
importmenu.add_command(label="Import Single Round", command=donothing)
importmenu.add_command(label="Import Screenshot", command=donothing)
menubar.add_cascade(label="Import", menu=importmenu)

datamenu = Menu(menubar, tearoff=0)
datamenu.add_command(label="New Round", command=donothing)
datamenu.add_command(label="New Driver", command=new_driver)
datamenu.add_separator()
datamenu.add_command(label="Edit Round", command=donothing)
datamenu.add_command(label="Edit Driver", command=edit_driver)
datamenu.add_separator()
datamenu.add_command(label="View Results", command=results_viewer)

menubar.add_cascade(label="Data", menu=datamenu)

exportmenu = Menu(menubar, tearoff=0)
exportmenu.add_command(label="Export Round List", command=donothing)
exportmenu.add_command(label="Export Round Results", command=donothing)
exportmenu.add_separator()
exportmenu.add_command(label="Export Driver List", command=donothing)
exportmenu.add_command(label="Export Driver Points", command=donothing)
menubar.add_cascade(label="Export", menu=exportmenu)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help Index", command=donothing)
helpmenu.add_command(label="About...", command=donothing)
menubar.add_cascade(label="Help", menu=helpmenu)

# Main Window
seriesinfoframe = LabelFrame(root, relief=RIDGE)
seriesinfoframe.grid(row=0, column=0, columnspan=2, padx=10, pady=(15, 10), sticky=N + E + S + W)
Label(seriesinfoframe, textvariable=league_name, font=("", 18)).grid(row=0, column=0, padx=5, pady=5, sticky=W)
Label(seriesinfoframe, textvariable=series_name, font=("", 14)).grid(row=1, column=0, padx=5, pady=5, sticky=W)
# logo_label = Label(seriesinfoframe, image=league_logo)
# logo_label.grid(row=0, column=1, rowspan=2, sticky=NE)

topdriversframe = LabelFrame(root, text="Top 15 Drivers", relief=SUNKEN)
topdriversframe.grid(row=2, column=0, padx=10, pady=10, sticky=NW)
notopdrivers = Label(topdriversframe, text="No Driver Entries")


def top_drivers_main(dl):
    # Writes top drivers
    # Top Drivers Headings.

    global notopdrivers
    if dl:
        notopdrivers.destroy()
        Label(topdriversframe, text="Pos", padx=2, pady=2, bg="gray90").grid(row=0, column=0, padx=(5, 0), sticky=E + W)
        Label(topdriversframe, text="Driver", padx=2, pady=2, bg="gray90").grid(row=0, column=1, sticky=E + W)
        Label(topdriversframe, text="Points", padx=2, pady=2, bg="gray90").grid(row=0, column=2, padx=(0, 5),
                                                                                sticky=E + W)

        # Top Drivers List
        for i in range(15):  # Rows
            top_pos_driver = dl[i].driver
            top_pos_points = dl[i].total_points
            i = i + 1

            top_pos = Label(topdriversframe, text=i, padx=2, pady=2)
            top_pos.grid(row=i, column=0, sticky=E + W)

            top_pos_driver = Label(topdriversframe, text=top_pos_driver, padx=8, pady=2)
            top_pos_driver.grid(row=i, column=1, sticky=E + W)

            top_pos_points = Label(topdriversframe, text=top_pos_points, padx=2, pady=2)
            top_pos_points.grid(row=i, column=2, sticky=E + W)

            for r in range(3):
                if (i % 2) == 0:
                    top_pos.configure(bg="gray99")
                    # top_pos.rowconfigure(topdriversframe, i, weight=1)
                    top_pos_driver.configure(bg="gray99")
                    top_pos_driver.rowconfigure(i, weight=1)
                    top_pos_points.configure(bg="gray99")
    else:
        notopdrivers.pack(padx=10, pady=(5, 10))


top_drivers_main(list_drivers(sort="points"))

# Quick Tools
quicktoolsframe = LabelFrame(root, text="Quick Tools")
quicktoolsframe.grid(row=2, column=1, padx=10, pady=10, sticky=NE)
qtpadx = 10
qtpady = 10
b1 = Button(quicktoolsframe, text="Results", command=results_viewer, width=20)
b1.pack(padx=qtpadx, pady=qtpady)
b2 = Button(quicktoolsframe, text="Import Round Results", command=donothing, width=20)
b2.pack(padx=qtpadx, pady=qtpady)
b3 = Button(quicktoolsframe, text="Export Round Results", command=donothing, width=20)
b3.pack(padx=qtpadx, pady=qtpady)
b4 = Button(quicktoolsframe, text="Export Top 15", command=donothing, width=20)
b4.pack(padx=qtpadx, pady=qtpady)
b5 = Button(quicktoolsframe, text="Export CSV", command=donothing, width=20)
b5.pack(padx=qtpadx, pady=qtpady)


def menu_state():
    if driver_objects:
        # QUICK TOOLS
        b1.config(state=NORMAL)
        b2.config(state=NORMAL)
        b3.config(state=NORMAL)
        b4.config(state=NORMAL)
        b5.config(state=NORMAL)

        filemenu.entryconfigure(2, state=NORMAL)

        importmenu.entryconfigure(0, state=NORMAL)
        importmenu.entryconfigure(2, state=NORMAL)
        importmenu.entryconfigure(3, state=NORMAL)

        datamenu.entryconfigure(0, state=NORMAL)
        datamenu.entryconfigure(1, state=NORMAL)
        datamenu.entryconfigure(3, state=NORMAL)
        datamenu.entryconfigure(4, state=NORMAL)
        datamenu.entryconfigure(6, state=NORMAL)


        exportmenu.entryconfigure(0, state=NORMAL)
        exportmenu.entryconfigure(1, state=NORMAL)
        exportmenu.entryconfigure(3, state=NORMAL)
        exportmenu.entryconfigure(4, state=NORMAL)

    else:
        # QUICK TOOLS
        b1.config(state=DISABLED)
        b2.config(state=DISABLED)
        b3.config(state=DISABLED)
        b4.config(state=DISABLED)
        b5.config(state=DISABLED)

        filemenu.entryconfigure(2, state=DISABLED)

        importmenu.entryconfigure(0, state=DISABLED)
        importmenu.entryconfigure(2, state=DISABLED)
        importmenu.entryconfigure(3, state=DISABLED)

        datamenu.entryconfigure(0, state=DISABLED)
        datamenu.entryconfigure(1, state=DISABLED)
        datamenu.entryconfigure(3, state=DISABLED)
        datamenu.entryconfigure(4, state=DISABLED)
        datamenu.entryconfigure(6, state=DISABLED)


        exportmenu.entryconfigure(0, state=DISABLED)
        exportmenu.entryconfigure(1, state=DISABLED)
        exportmenu.entryconfigure(3, state=DISABLED)
        exportmenu.entryconfigure(4, state=DISABLED)


menu_state()

root.resizable(False, False)
root.config(menu=menubar)
root.mainloop()
