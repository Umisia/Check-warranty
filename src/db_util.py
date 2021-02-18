import mysql.connector
import config
from logger import Logger

log = Logger(__name__).logger

class DB:
    def __init__(self, db_name):
        self.conn = mysql.connector.connect(
            host="localhost",
            user=config.db_user,
            password=config.db_pswd,
            database=db_name)
        self.cursor = self.conn.cursor(buffered=True)
        log.info(f"connected to {db_name}")

    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE orders (so_id BIGINT PRIMARY KEY, so_number VARCHAR(20), order_date DATE, dispatch_date DATE, billing_name VARCHAR(100), shipping_name VARCHAR(100), shipping_postcode VARCHAR(50), billing_postcode VARCHAR(50))")
        self.cursor.execute(
            "CREATE TABLE serial_numbers (id INT AUTO_INCREMENT PRIMARY KEY, sn VARCHAR(20),order_id BIGINT, FOREIGN key(order_id) REFERENCES orders(so_id))")
        self.cursor.execute(
            "CREATE TABLE extended_warranty (id INT AUTO_INCREMENT PRIMARY KEY, order_id BIGINT, warranty INT, FOREIGN key(order_id) REFERENCES orders(so_id))")
        self.cursor.execute("SHOW TABLES")

    def insert_order(self, val: tuple):
        query = "INSERT INTO orders(so_id, so_number, order_date, dispatch_date, billing_name, shipping_name, billing_postcode, shipping_postcode) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        self.cursor.execute(query, val)
        self.conn.commit()
        log.info(f"{self.cursor.rowcount}, order inserted")

    def insert_serials(self, order_id: int, serials: list):
        values_to_insert = [(order_id, serials[i]) for i in range(0, len(serials))]
        query = "INSERT INTO serial_numbers(order_id, sn) VALUES (%s,%s)"
        self.cursor.executemany(query, values_to_insert)
        self.conn.commit()
        log.info(f"{self.cursor.rowcount}, serials inserted\n")

    def insert_warranty(self, order_id: int, val: int):
        values = (order_id, val)
        query = "INSERT INTO extended_warranty(order_id, warranty) VALUES (%s,%s)"
        self.cursor.execute(query, values)
        self.conn.commit()
        log.info(f"{self.cursor.rowcount}, warranty info inserted")

    def check_if_in_db(self, order_no: str):
        self.cursor.execute(f"SELECT COUNT(1) FROM orders WHERE so_number = '{order_no}'")
        for x in self.cursor:
            return x[0]

    def find(self, column: str, val: str):
        log.debug(column, val)
        self.cursor.execute(f'''
        select orders.so_id, orders.so_number, orders.order_date, orders.dispatch_date, extended_warranty.warranty
        from orders
        left join serial_numbers on orders.so_id = serial_numbers.order_id
        left join extended_warranty on orders.so_id  = extended_warranty.order_id
        where {column} like "%{val}%"
        group by orders.so_id
        ''')
        return self.cursor.fetchall()

    def delete_from_db(self, table, column, value):
        self.cursor.execute(f"DELETE FROM {table} WHERE {column} = '{value}'")
        self.conn.commit()

    def update_postcode(self, so_id, val):
        self.cursor.execute("UPDATE orders SET shipping_postcode=%s WHERE so_id=%s", (val, so_id))
        self.conn.commit()
        log.info(f"{self.cursor.rowcount}, order updated")

    def update_addresses(self, so_id, val):
        self.cursor.execute("UPDATE orders SET billing_name=%s, billing_postcode=%s, shipping_name=%s, shipping_postcode=%s WHERE so_id=%s", (*val, so_id))
        self.conn.commit()
        log.info(f"{self.cursor.rowcount}, order updated")

    def find_order_by_no(self, value):
        self.cursor.execute(f"SELECT orders.so_number, orders.order_date, orders.dispatch_date, orders.so_id FROM orders WHERE so_number = '{value}'")
        if self.cursor.rowcount:
            return [result for result in self.cursor]

    def find_order_by_sn(self, sn):
        self.cursor.execute(f"SELECT orders.so_number, orders.order_date, orders.dispatch_date, orders.so_id FROM orders, serial_numbers WHERE orders.so_id = serial_numbers.order_id AND serial_numbers.sn = '{sn}'")
        if self.cursor.rowcount:
            return [result for result in self.cursor]

    def insert_sn_into_order(self, order_id, sn):
        self.cursor.execute(f"INSERT INTO serial_numbers(sn, order_id) VALUES ({sn}, {order_id})")
        self.conn.commit()

    def close_db(self):
        self.cursor.close()
        self.conn.close()

    # def update_rows():
    #     mycursor.execute("SELECT orders.so_number, orders.so_id, billing_name FROM orders")
    #     bazadanych = []
    #     for result in mycursor:
    #     #     print(type(result))
    #         bazadanych.append(result)

    #     for result in bazadanych:
    #         print(result[0])
    #         if result[2] == None: #row still to do
    #             print("robimy", result[0])
    #             if "SO-" in result[0]:
    #                 *addresses, info, warranties = inv_orders(result[1])
    #             elif "LP-" in result[0]:
    #                 print("LP ", result[0])
    #                 *addresses, info, warranties = crm_orders(result[1])
    #             print(addresses, result[1])
    #             update_addresses(addresses, result[1])

    #             print(warranties)
    #             if warranties:
    #                 print("warranties")
    #                 warranties.insert(0, result[0])
    #                 warranties.insert(0, result[1])  
    #                 print(info)
    #                 if info:
    #                     warranties.insert(0, info)
    #                 print(warranties)
    #                 add_to_csv(warranties)
    #     #                 input()
    #             else:
    #                 print("no warranties, next!")

# def reset_db():
#     def delete_db(name):
#         cursor.execute(f"DROP DATABASE {name}")
#
#     def create_db(name):
#         cursor.execute(f"CREATE DATABASE {name}")
#
#     conn = mysql.connector.connect(
#         host="localhost",
#         user=config.db_user,
#         password=config.db_pswd)
#     cursor = conn.cursor(buffered=True)
#     delete_db('serialnumbers')
#     create_db("serialnumbers")
#     mydb = DB('serialnumbers')
#     mydb.create_tables()
# reset_db()