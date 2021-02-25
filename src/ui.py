import tkinter
from tkinter import ttk
import datetime, datedelta
import webbrowser
import subprocess
import threading
from excel_util import Spreadsheet
from db_util import DB
import config
import collections
from tkinter import messagebox
from logger import Logger


def upload():
    wb = Spreadsheet(config.spreadsheet_path)
    lastrow = wb.get_last_row()
    lastcol = wb.get_last_column()
    for row in range(2, lastrow + 1):
        so_id = wb.get_cell(row, 1)
        if so_id.isdigit():
            warranty = wb.get_cell(row, lastcol)
            mydb.insert_warranty(so_id, warranty)
            log.info(f"writing warranty {so_id}, {warranty}, to: {row}{lastcol}")

def update_db():
    thread = threading.Thread(target=run_batch)
    thread.start()

def run_batch():
    p = subprocess.Popen(config.batch_path, creationflags=subprocess.CREATE_NEW_CONSOLE)
    p.wait()
def search(value):
    Result = collections.namedtuple("Result", "column so_id so_no order_date dispatch_date extra_warranty",
                                    defaults=(None,))
    columns_to_check = ("ops_orders.so_number",
                        "ops_orders.shipping_name",
                        "ops_orders.billing_name",
                        "ops_orders.billing_postcode",
                        "ops_orders.shipping_postcode",
                        "ops_serial_numbers.sn")
    finds = []
    for column in columns_to_check:
        try:
            r = mydb.find(column, value)
        except:
            messagebox.showinfo("Alert", "Incorrect value")
            finds.clear()
            break
        for tuple_ in r:
            result = (column,) + tuple_
            finds.append(Result(*result))
    return finds

def create_link(result):
    order_link = None
    if "LP" in result.so_no:  # CMR order
        order_link = f"https://crm.zoho.com/crm/{config.crm_org}/tab/SalesOrders/{result.so_id}"
    elif "SO" in result.so_no:  # Inventory order
        order_link = f"https://inventory.zoho.com/app#/salesorders/{result.so_id}?filter_by=Status.All&per_page=200&sort_column=last_modified_time&sort_order=D"

    add_link_label(order_link)

def add_link_label(link):
    labels.append(tkinter.Label(scrollable_frame, text="order_link", fg="blue", cursor="hand2", width=20, anchor="w"))
    labels[-1].grid(column=0, row=len(labels))
    labels[-1].bind("<Button-1>", lambda e: callback(link))

def format_exact_match(result_tuple):
    add_label(result_tuple.so_no)
    create_link(result_tuple)
    add_label("order date: " + str(result_tuple.order_date))
    add_label("dispatch date: " + str(result_tuple.dispatch_date))

    if result_tuple.extra_warranty:
        log.debug(f"extra warranty: {result_tuple.extra_warranty}")
        warranty_until = result_tuple.dispatch_date + datedelta.datedelta(years=result_tuple.extra_warranty)
    else:
        warranty_until = result_tuple.dispatch_date + datedelta.YEAR

    if warranty_until >= datetime.date.today():
        add_label("IN WARRANTY", color="green")
    else:
        add_label("OUT OF WARRANTY", color="red")
    add_label("warranty unitl: " + str(warranty_until))

def find_orders():
    input_val = entry.get()
    if len(input_val) >= 4:
        clear_labels()
        search_finds = search(input_val)
        labels = []
        add_label(f"Results for '{input_val}':", color="purple4")

        log.info(search_finds)
        for find in search_finds:
            if find.column == "ops_orders.so_number" or find.column == "ops_serial_numbers.sn":
                format_exact_match(find)
                labels.append(find.so_no)
            else:
                sono = find.so_no
                if sono not in labels:
                    labels.append(sono)
                    add_label(sono)
                    create_link(find)
    else:
        messagebox.showinfo("Alert", "Incorrect value")

def add_label(val, color="black"):
    labels.append(tkinter.Label(scrollable_frame, text=val, width=20, anchor="w", fg=color))
    labels[-1].grid(column=0, row=len(labels))
    if len(labels) >= 15:
        scrollbar.pack(side="right", fill="y")

def clear_labels():
    entry.delete(0, 'end')
    [lab.destroy() for lab in labels]
    del labels[:]
    scrollbar.pack_forget()

def callback(url):
    webbrowser.open_new(url)

def on_closing():
    window.destroy()
    mydb.close_db()


log = Logger(__name__).logger
mydb = DB("warranty_database")

window = tkinter.Tk()
window.title("Find order")
window.minsize(200, 200)

window.protocol("WM_DELETE_WINDOW", on_closing)
frame = ttk.Frame(window)

canvas = tkinter.Canvas(frame, width=200, highlightthickness=0)
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

entry = tkinter.Entry(scrollable_frame)
entry.grid(column=0, row=0)

button_find = tkinter.Button(scrollable_frame, text="Search", command=find_orders)
button_find.grid(column=1, row=0)

labels = []
link_labels = []

frame.pack()
canvas.pack(side="left", fill="both", expand="true")

bottom = tkinter.Frame(window)
bottom.pack(side="bottom")

button_update = tkinter.Button(bottom, text="Update DB", command=update_db, bg="firebrick1")
button_update.grid(column=0, row=0)

button_addwarranty = tkinter.Button(bottom, text="Upload", command=upload, bg="hotpink3")
button_addwarranty.grid(column=1, row=0, padx=(10, 0))
window.mainloop()
