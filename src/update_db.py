import threading
import zoho_oauth
import config
import requests, json
from order import InvOrder, CrmOrder
from excel_util import Spreadsheet
from db_util import DB
from logger import Logger
import argparse

def get_crm_orders(page):
    head = {
        'Authorization': 'Zoho-oauthtoken ' + access_token}
    response = requests.get(f"https://www.zohoapis.com/crm/v2/Sales_Orders?page={page}&per_page=200", headers=head)
    json_response = json.loads(response.text)
    log.debug(f"get_crm_orders response: {json_response}")
    return json_response

def get_inv_orders(page):
    request_head = {
        'orgId': config.org_id,
        'Authorization': 'Zoho-oauthtoken ' + access_token}
    response = requests.get(
        "https://inventory.zoho.com/api/v1/salesorders?filter_by=Status.Closed&page=" + str(page) + "&per_page=200",
        headers=request_head)
    json_response = json.loads(response.text)
    log.debug(f"get_inv_orders response: {json_response}")
    return json_response["salesorders"]

def refresh_token_thread(toks):
    log.info("--------------------------------------------------------------------")
    log.info(f"refresh timer for token started: {toks}")
    global thread
    thread = threading.Timer(3000.0, refresh_token_thread, [toks])  # 50minutes
    thread.start()
    global access_token
    log.info("===============================refreshing token======================================")
    access_token = zoho_oauth.refresh_token(toks)

def add_data(data, db, excel):
    order_data = data.so_id, data.so_no, data.order_date, data.dispatch_date, data.bill_name, data.ship_name, data.bill_postcode, data.ship_postcode
    log.info(order_data)
    db.insert_order(order_data)# add order to db, table:ops_orders # needs values in tuple

    if data.serials:# add serial numbers to db, table:ops_serial_numbers
        try:
            db.insert_serials(data.so_id, data.serials)  # so_id:int, serials:list
        except:
            db.delete_from_db("ops_orders", "so_id", data.so_id)  # undo order insertion, so the order can be catched again as a new one
            raise Exception(f"Failed to add serials for: {data.so_no}:{data.so_id}")
    else:
        log.info(f"no serials")

    # matches for warranties found
    if data.warranties:  # list
        log.info(f"warranties: {data.warranties}")
        warranties_matched = ', '.join(data.warranties)
        #when sku found insert to db, otherwise write to spreadsheet
        db_written = False
        for sku, period in config.skus_warr.items():
            if sku in warranties_matched:
                db.insert_warranty(data.so_id, period)
                db_written = True
                break
        if not db_written:
            excel.write_data(data.warranties)

def do_inv_orders(page_to, db, excel):
    token = config.inv_token
    refresh_token_thread(token)
    for page in range(1, page_to+1):
        log.info(f"page: {page}")
        try:
            orders_data = get_inv_orders(page)
        except ValueError:
            log.info(f"No more pages. {page - 1} pages done.")
            break
        for order in orders_data:
            if mydb.check_if_in_db(order['salesorder_number']) == 0:  # so number not in database
                log.info(f"order not in db: {order['salesorder_number']}")
                new_order = InvOrder(order['salesorder_id'], access_token)
                new_order.get_serials()
                add_data(new_order, db, excel)
            else:
                log.info(f"order already in db: {order['salesorder_number']}: skipped")
            order_link = f"https://inventory.zoho.com/app#/salesorders/{order['salesorder_id']}?filter_by=Status.All&per_page=200&sort_column=last_modified_time&sort_order=D"
            log.info(order_link)
            log.info("\n")
    thread.cancel()

def do_crm_orders(page_to, db, excel):
    token = config.crm_token
    refresh_token_thread(token)
    for page in range(1, page_to+1):
        log.info(f"page: {page}")
        try:
            orders_data = get_crm_orders(page)
        except ValueError:
            log.info(f"No more pages. Last one: {page - 1} done.")
            break
        for order in orders_data["data"]:
            if order["Status"] == "Shipped" or order["Status"] == "Invoiced":
                if mydb.check_if_in_db(order["Sales_Order_Number"]) == 0:  # so number not in database
                    log.info(f"order not in db: {order['Sales_Order_Number']}")
                    new_order = CrmOrder(order['id'], access_token)
                    new_order.get_serials()
                    add_data(new_order, db, excel)
                    log.info(f"order {order['Sales_Order_Number']} added")
                else:
                    log.info(f"order already in db: {order['Sales_Order_Number']}: skipped")
            else:
                log.info(f"Order {order['Sales_Order_Number']} skipped: Status:{order['Status']}")
            order_link = f"https://crm.zoho.com/crm/org19832112/tab/SalesOrders/{order['id']}"
            log.info(order_link)
            log.info("\n")
    thread.cancel()

log = Logger(__name__).logger
mydb = DB("warranty_database")

if __name__ == '__main__':
    excel = Spreadsheet(config.spreadsheet_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--populate', help='populate empty database', action='store_true')
    args = parser.parse_args()

    if args.populate:
        log.info("populate")
        pages = 50
        do_crm_orders(pages, mydb, excel)
        do_inv_orders(pages, mydb, excel)
    else:
        log.info("update")
        pages = 1
        do_inv_orders(pages, mydb, excel)
    mydb.close_db()
    excel.save()
    excel.close()