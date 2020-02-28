import requests
from rethinkdb import RethinkDB
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
import datetime

# Initialize library objects
r = RethinkDB()
master = Tk()


def get_date():
    return datetime.date.today().strftime("%d/%m/%y")


# Database connection method
def db_connect():
    config = open("login.txt").readlines()
    try:
        conn = r.connect(host="localhost", port=28015, db="SG", user=config[0].rstrip(), password=config[1].rstrip())
    except:
        print("Could not connect to database")
        sys.exit()
    return conn


# Connect to database
conn = db_connect().repl()


# Fetch name from specified table
def get_data(table, name):
    # cursor = r.table(table).filter({"user": name}).run()
    cursor = r.table(table).filter(lambda doc:
        doc["user"].match("(?i)^"+name+"$")
    ).run()
    return list(cursor)


def get_table(table):
    cursor = r.table(table).run()
    return list(cursor)


# Set string variables
def set_signaller_labels(data):
    global signaller_vars
    global signaller_notes
    global signaller_notes_dict
    if len(data) < 1:
        return
    result = data[0]
    for k, v in result.items():
        print(k, v)
        signaller_vars[k].set(v)
    signaller_vars["notes"].set(lookup_note_message(data[0]["notes"], signaller_notes_dict))
    signaller_notes_option.set(signaller_vars["notes"].get())


def lookup_signaller():
    global signaller_input
    data = get_data("signallers", signaller_input.get())
    set_signaller_labels(data)


def mark_training(type, complete):
    global signaller_name
    if complete:
        if messagebox.askokcancel("Confirm", "Mark " + type + " as complete?"):
            r.table("signallers").filter({"user": signaller_name.get()}).update({type: get_date()}).run()
    else:
        if messagebox.askokcancel("Confirm", "Mark " + type + " as incomplete?"):
            r.table("signallers").filter({"user": signaller_name.get()}).update({type: "Incomplete"}).run()


def complete_theory():
    mark_training("theory", True)


def incomplete_theory():
    mark_training("theory", False)


def complete_practical():
    mark_training("practical", True)


def incomplete_practical():
    mark_training("practical", False)


def complete_assessment():
    mark_training("assessment", True)


def incomplete_assessment():
    mark_training("assessment", False)

def lookup_strikes():
    global strikes_input
    data = get_data("strikes", strikes_input.get())
    display_strikes(data)


def get_strikes():
    data = get_table("strikes")
    display_strikes(data)


def display_strikes(data):
    global strikes_tree
    strikes_tree.delete(*strikes_tree.get_children())
    for i in data:
        print(i)
        vals = [i["user"], i["hr"], i["type"], i["reason"], i["evidence"]]
        strikes_tree.insert("", END, values=vals)


def copy_evidence(e):
    global strikes_tree
    global master
    index = strikes_tree.focus()
    selection = strikes_tree.item(index)["values"][4]
    print(selection)
    master.clipboard_clear()
    master.clipboard_append(selection)
    master.update()


def open_create_strike_window():
    global strike_types
    global strike_user_input
    global strike_hr_input
    global strike_type_input
    global strike_reason_input
    global strike_evidence_input

    create_strike_window = Toplevel()

    Label(create_strike_window, text="User").grid(row=0, column=0)
    Label(create_strike_window, text="HR").grid(row=1, column=0)
    Label(create_strike_window, text="Type").grid(row=2, column=0)
    Label(create_strike_window, text="Reason").grid(row=3, column=0)
    Label(create_strike_window, text="Evidence").grid(row=4, column=0)

    strike_user_input = Entry(create_strike_window)
    strike_hr_input = Entry(create_strike_window)
    strike_type_input = StringVar()
    OptionMenu(create_strike_window, strike_type_input, *strike_types).grid(row=2, column=1)
    strike_reason_input = Entry(create_strike_window)
    strike_evidence_input = Entry(create_strike_window)

    strike_user_input.grid(row=0, column=1)
    strike_hr_input.grid(row=1, column=1)
    strike_reason_input.grid(row=3, column=1)
    strike_evidence_input.grid(row=4, column=1)

    Button(create_strike_window, text="Add Strike", command=create_strike).grid(row=5, columnspan=2)


def create_strike():
    global strike_user_input
    global strike_hr_input
    global strike_type_input
    global strike_reason_input
    global strike_evidence_input

    strike_inputs = dict()
    strike_inputs["user"] = strike_user_input.get()
    strike_inputs["hr"] = strike_hr_input.get()
    strike_inputs["type"] = strike_type_input.get()
    strike_inputs["reason"] = strike_reason_input.get()
    strike_inputs["evidence"] = strike_evidence_input.get()

    for i in strike_inputs.values():
        if i == "":
            messagebox.showerror("Missing Fields", "Please fill out ALL fields to create a strike")
            return
    if messagebox.askokcancel("Confirm", "Add Strike?"):
        r.table("strikes").insert(strike_inputs).run()
    return


def update_signaller():
    global signaller_notes_option
    global signaller_notes_dict
    global signaller_vars
    print(lookup_note_value(signaller_notes_option.get(), signaller_notes_dict), get_date(), signaller_vars["user"].get())
    print(r.table("signallers").filter({"user": signaller_vars["user"].get()})
          .update({"updated": get_date(), "notes": lookup_note_value(signaller_notes_option.get(), signaller_notes_dict)}).run())


def update_user():
    global username_input

    old_username = username_input.get()
    data = get_data("signallers", old_username)
    if len(data) < 1:
        return
    user_id = data[0]["id"]
    resp = requests.get("https://api.roblox.com/users/" + str(user_id)).json()
    print(resp)
    if "Username" not in resp:
        return
    new_username = resp["Username"]
    if old_username == new_username:
        return
    if messagebox.askokcancel("Confirm", "Change user " + old_username + " to " + new_username + "?"):
        r.table("signallers").filter({"user": old_username}).update({"user": new_username}).run()
        r.table("strikes").filter({"user": old_username}).update({"user": new_username}).run()


def open_username_updater():
    username_window = Toplevel()

    global username_input

    Label(username_window, text="Input Old Username").grid(row=0, column=0)
    input = Entry(username_window, textvariable=username_input)
    input.grid(row=0, column=1)
    input.bind("<Return>", (lambda event: update_user()))
    Button(username_window, text="Update", command=update_user).grid(row=0, column=2)


def open_signallers_window():
    signallers_window = Toplevel()
    # Set up labels for columns
    global signaller_name
    global signaller_id
    global signaller_notes
    global signaller_notes_option
    global signaller_updated
    global signaller_date
    global signaller_input
    global signaller_theory
    global signaller_practical
    global signaller_assessment

    Label(signallers_window, text="Name").grid(row=0, column=0)
    Label(signallers_window, text="ID").grid(row=0, column=1)
    Label(signallers_window, text="Notes").grid(row=0, column=2)
    Label(signallers_window, text="Date").grid(row=0, column=3)
    Label(signallers_window, text="Updated").grid(row=0, column=4)
    Label(signallers_window, text="Theory").grid(row=0, column=5, columnspan=2)
    Label(signallers_window, text="Practical").grid(row=0, column=7, columnspan=2)
    Label(signallers_window, text="Assessment").grid(row=0, column=9, columnspan=2)

    # Set up labels to display data
    Label(signallers_window, textvariable=signaller_name).grid(row=1, column=0)
    Label(signallers_window, textvariable=signaller_id).grid(row=1, column=1)
    Label(signallers_window, textvariable=signaller_notes).grid(row=1, column=2)
    Label(signallers_window, textvariable=signaller_date).grid(row=1, column=3)
    Label(signallers_window, textvariable=signaller_updated).grid(row=1, column=4)
    Label(signallers_window, textvariable=signaller_theory).grid(row=1, column=5, columnspan=2)
    Label(signallers_window, textvariable=signaller_practical).grid(row=1, column=7, columnspan=2)
    Label(signallers_window, textvariable=signaller_assessment).grid(row=1, column=9, columnspan=2)

    # Entry and Submission
    signaller_input = Entry(signallers_window)
    signaller_input.bind("<Return>", (lambda event: lookup_signaller()))
    signaller_input.grid(row=3, column=0)
    Button(signallers_window, text="Search", command=lookup_signaller).grid(row=3, column=1)

    # Updating notes
    signaller_notes_menu = OptionMenu(signallers_window, signaller_notes_option, *list(signaller_notes_dict.keys()))
    signaller_notes_menu.grid(row=3, column=2)
    Button(signallers_window, text="Complete Theory", command=complete_theory).grid(row=3, column=5)
    Button(signallers_window, text="Incomplete Theory", command=incomplete_theory).grid(row=3, column=6)
    Button(signallers_window, text="Complete Practical", command=complete_practical).grid(row=3, column=7)
    Button(signallers_window, text="Incomplete Practical", command=incomplete_practical).grid(row=3, column=8)
    Button(signallers_window, text="Complete Assessment", command=complete_assessment).grid(row=3, column=9)
    Button(signallers_window, text="Incomplete Assessment", command=incomplete_assessment).grid(row=3, column=10)
    Button(signallers_window, text="Update", command=update_signaller).grid(row=3, column=3)


def open_strikes_window():
    strikes_window = Toplevel()

    global strikes_tree
    global strikes_input
    strikes_tree = Treeview(strikes_window, column=("column1", "column2", "column3", "column4", "column5"),
                            show="headings")
    strikes_tree.heading("#1", text="Username")
    strikes_tree.heading("#2", text="HR")
    strikes_tree.heading("#3", text="Type")
    strikes_tree.heading("#4", text="Reason")
    strikes_tree.heading("#5", text="Evidence")
    strikes_tree.bind("<Button-2>", copy_evidence)
    strikes_tree.grid(row=0, columnspan=4)

    strikes_input = Entry(strikes_window)
    strikes_input.bind("<Return>", (lambda event: lookup_strikes()))
    strikes_input.grid(row=1, column=0)
    Button(strikes_window, text="Search", command=lookup_strikes).grid(row=1, column=1)
    Button(strikes_window, text="Display All", command=get_strikes).grid(row=1, column=2)
    Button(strikes_window, text="Add Strike/Warning", command=open_create_strike_window).grid(row=1, column=3)


def lookup_note_message(value, note_dict):
    for k, v in note_dict.items():
        if v == value:
            return k
    return ""


def lookup_note_value(key, note_dict):
    if key in note_dict:
        return note_dict[key]
    return ""


# Set up signaller string variables
signaller_id = StringVar()
signaller_name = StringVar()
signaller_notes = StringVar()
signaller_date = StringVar()
signaller_updated = StringVar()
signaller_theory = StringVar()
signaller_practical = StringVar()
signaller_assessment = StringVar()
signaller_notes_option = StringVar()

signaller_vars = dict()
signaller_vars["id"] = signaller_id
signaller_vars["user"] = signaller_name
signaller_vars["notes"] = signaller_notes
signaller_vars["date"] = signaller_date
signaller_vars["updated"] = signaller_updated
signaller_vars["theory"] = signaller_theory
signaller_vars["practical"] = signaller_practical
signaller_vars["assessment"] = signaller_assessment

username_input = StringVar()

signaller_notes_dict = {
    "": "",
    "[U] Transferred to Manager": "manager",
    "[U] Transferred to Director": "director",
    "[U] Transferred to PRA": "pra",
    "[U] Transferred to SDS": "sds",
    "[U] Transferred to LD": "ld",
    "[P] Promoted to SSG": "ssg",
    "[S] Promoted to SG": "sg",
    "[X] Left": "left",
    "[X] Failed Assessments": "failed",
    "[X] Removed": "removed",
    "None": ""
}

strike_types = ["", "warning", "strike"]

# Create menu
Button(master, text="Signallers", command=open_signallers_window).grid(row=0, column=0)
Button(master, text="Strikes", command=open_strikes_window).grid(row=0, column=1)
Button(master, text="Update Username", command=open_username_updater).grid(row=0, column=2)

# Call Tkinter main loop to run the GUI
mainloop()
