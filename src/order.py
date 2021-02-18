import time
import config
import docx, io, requests, json
import pandas as pd
from logger import Logger

log = Logger(__name__).logger


def matcher(item, flag):
    def matcher_helper(item, seq):
        for s in seq:
            if s.lower() in item.lower():
                log.debug(f"item: {item}: True. Matched to: {s}")
                return True
            log.debug(f"item {item}: False")
        return False

    if flag == 'warranty':
        matches = 'extended warranty', 'classcare', 'extended', 'additional', 'warranty', 'extension'
        not_matches = 'warranty replacement', 'one tablet per', 'additional software', 'shipping for classcare', 'claimed under warranty', 'additional payment', 'additional charge'
    elif flag == 'sn':
        matches = config.models
        not_matches = config.not_models

    if matcher_helper(item, matches) and item not in not_matches:
        return True
    else:
        return False

def validate_sn(sn):
    if len(sn) > 5 and any(char.isdigit() for char in sn):
        if matcher(sn, 'sn'):
            return sn.upper()

def get_xls_content(bytes_obj):
    excel = pd.ExcelFile(io.BytesIO(bytes_obj))
    df = excel.parse('Sheet1').dropna(how='all').copy().reset_index().drop(0)
    df_list = df.values.tolist()
    flat_list = [str(item) for sublist in df_list for item in sublist]
    log.debug(flat_list)
    return flat_list

def get_docx_content(bytes_obj):
    time.sleep(0.2)
    doc = docx.Document(io.BytesIO(bytes_obj))
    wholedoc = []
    time.sleep(0.2)
    for para in doc.paragraphs:
        wholedoc.append(para.text)
        log.debug(f"wholedoc: {wholedoc}")
    return wholedoc

class InvOrder:
    def __init__(self, ord_id, oauth_token):
        self.so_id = ord_id
        self.token = oauth_token
        self.request_head = {'orgId': config.org_id, 'Authorization': 'Zoho-oauthtoken ' + self.token}
        self.data = self.get_data()
        self.serials = []

    def get_data(self):
        response = requests.get("https://inventory.zoho.com/api/v1/salesorders/" + str(self.so_id),
                                headers=self.request_head)
        return json.loads(response.text)

    @property
    def so_no(self):
        return self.data["salesorder"]["salesorder_number"]

    @property
    def order_date(self):
        return self.data["salesorder"]["date"]

    @property
    def dispatch_date(self):
        if self.data["salesorder"]["shipment_date"]:
            return self.data["salesorder"]["shipment_date"]
        try:
            return self.data["salesorder"]['packages'][0]['shipment_date']
        except:
            return self.order_date

    @property
    def bill_name(self):
        return self.data['salesorder']['customer_name']

    @property
    def bill_postcode(self):
        return self.data['salesorder']['billing_address']['zip']

    @property
    def ship_name(self):
        if self.bill_postcode == self.ship_postcode:
            return self.bill_name
        return self.data['salesorder']['shipping_address']['attention'] or \
               self.data['salesorder']['shipping_address']['address'].split("\n")[0] or self.bill_name

    @property
    def ship_postcode(self):
        return self.data['salesorder']['shipping_address']['zip'] or self.bill_postcode

    @property
    def warranties(self):
        warranty_match = []
        important_info = None

        reference = self.data['salesorder']['reference_number']
        if reference and matcher(reference.lower(), 'warranty'):
            warranty_match.append(reference)

        line_items = self.data['salesorder']['line_items']
        for item in line_items:
            desc = item['description']
            name = item['name']
            if (desc and matcher(desc.lower(), 'warranty')) or (name and matcher(name.lower(), 'warranty')):
                warranty_match.append(item['name'].lower())
                warranty_match.append(item['sku'].lower())
                warranty_match.append(desc)

        custom_fields = self.data['salesorder']['custom_fields']
        for field in custom_fields:
            if field['label'] == 'Important Information':
                important_info = field['value'].lower()
                if matcher(important_info, 'warranty'):
                    warranty_match.append(important_info)

        if len(warranty_match) > 0:
            warranty_match.insert(0, str(self.so_id))
            if important_info:
                warranty_match.insert(1, important_info)
        return warranty_match

    def get_serials(self):
        ids_and_names = self.get_ids_filenames()
        log.info(ids_and_names)
        for doc_id, filename in ids_and_names.items():
            if "numbers" in filename.lower() or "serial" in filename.lower() or self.so_no.lower() in filename.lower() or \
                    self.so_no.split('-')[1] in filename:
                log.info(f"serials file found: {filename}")
                file_content = self.get_file_content(doc_id, filename)
                self.extract_serials(file_content)

    def extract_serials(self, input_list):
        log.debug(f"input_list: {input_list}")
        if input_list:
            for element in input_list:
                log.debug(f"extract_serials: element: {element}")
                if " " in element or "\n" in element or "\t" in element:
                    log.debug("extract_serials: recursion")
                    self.extract_serials(element.split())
                else:
                    log.debug(f"extract_serials: validate_sn: element: {element}")
                    sn = validate_sn(element)
                    if sn:
                        self.serials.append(sn)
                        log.debug(f"serials appended: {sn}")

    def get_ids_filenames(self):
        documents = self.data["salesorder"]["documents"]
        ids_names = {}
        for doc in documents:
            ids_names[doc["document_id"]] = doc["file_name"]
        log.debug(f"documents ids and names: {ids_names}")
        return ids_names

    def get_file_content(self, doc_id, file_name):
        log.debug(doc_id, file_name)
        response = requests.get(
            "https://inventory.zoho.com/api/v1/salesorders/" + str(self.so_id) + "/documents/" + doc_id,
            headers=self.request_head, stream=True)
        doc_bytes = response.content
        content = None

        if ".txt" in file_name:
            content = doc_bytes.decode("utf-8").split()
        elif ".xls" in file_name:
            log.debug("XLS")
            content = get_xls_content(doc_bytes)
        elif ".docx" in file_name:
            log.info("DOCX")
            content = get_docx_content(doc_bytes)
        return content

    def log_atributes(self):
        log.info(f"so-number: {self.so_no}")
        log.info(f"so_id: {self.so_id}")
        log.info(f"warranty: {self.warranties}")
        log.info(f"serials: {self.get_serials()}")
        log.info(f"{self.bill_name}, {self.bill_postcode}")
        log.info(f"{self.ship_name}, {self.ship_postcode}")
        log.info(f"{self.order_date}, {self.dispatch_date}")


class CrmOrder:
    def __init__(self, ord_id, oauth_token):
        self.token = oauth_token
        self.so_id = ord_id
        self.request_head = {'Authorization': 'Zoho-oauthtoken ' + self.token}
        self.data = self.get_order_details()["data"][0]
        self.serials = []

    def get_order_details(self):
        response = requests.get(f"https://www.zohoapis.com/crm/v2/Sales_Orders/{self.so_id}", headers=self.request_head)
        return json.loads(response.text)

    @property
    def so_no(self):
        return self.data["Sales_Order_Number"]

    @property
    def order_date(self):
        return self.data["Created_Time"][:self.data["Created_Time"].index("T")]

    @property
    def dispatch_date(self):
        return self.data["Date_of_Dispatch"] or self.order_date

    def get_account(self, account_id):
        response = requests.get(f"https://www.zohoapis.com/crm/v2/Accounts/{account_id}", headers=self.request_head)
        return json.loads(response.text)

    @property
    def bill_name(self):
        if self.data['Account_Name']:
            account_info = self.get_account(self.data['Account_Name']['id'])['data'][0]
            bill_name = account_info['Account_Name']
        else:
            bill_name = self.data['Billing_Company']
        return bill_name

    @property
    def bill_postcode(self):
        if self.data['Account_Name']:
            account_info = self.get_account(self.data['Account_Name']['id'])['data'][0]
            bill_postcode = account_info['Billing_Code'] or account_info['Shipping_Code']
        else:
            bill_postcode = self.data['Billing_Code']
        return bill_postcode

    @property
    def ship_name(self):
        if self.data['End_User_Organisation']:
            account_info = self.get_account(self.data['End_User_Organisation']['id'])['data'][0]
            ship_name = account_info['Account_Name']
        else:
            ship_name = self.data['Shipping_Company'] or self.bill_name
        return ship_name

    @property
    def ship_postcode(self):
        if self.data['End_User_Organisation']:
            account_info = self.get_account(self.data['End_User_Organisation']['id'])['data'][0]
            ship_postcode = account_info['Shipping_Code'] or account_info['Billing_Code']
        else:
            ship_postcode = self.data['Shipping_Code'] or self.bill_postcode
        return ship_postcode

    @property
    def warranties(self):
        warranty_match = []
        products = self.data["Product_Details"]
        for product in products:
            prod_desc = product["product_description"]
            if prod_desc and matcher(prod_desc.lower(), 'warranty'):
                warranty_match.append(product['product']['Product_Code'].lower())
                warranty_match.append(product['product']['name'].lower())
                warranty_match.append(prod_desc)
        description = self.data["Description"] or None
        if description and matcher(description.lower(), 'warranty'):
            warranty_match.append(description)
        subject = self.data["Subject"]
        if subject and matcher(subject.lower(), 'warranty'):
            warranty_match.append(subject)
        if len(warranty_match) > 0:
            warranty_match.insert(0, str(self.so_id))
            if description:
                warranty_match.insert(1, description)
        return warranty_match

    def get_serials(self):
        if self.data["Serial_Numbers"]:
            serial_nos = self.data["Serial_Numbers"]
            log.debug(f'{serial_nos}')
            for element in serial_nos.split():
                log.debug(f"element: {element}")
                sn = validate_sn(element)
                if sn:
                    self.serials.append(sn)
                    log.debug(f"serials appended: {sn}")

    def log_atributes(self):
        log.info(f"so-number: {self.so_no}")
        log.info(f"so_id: {self.so_id}")
        log.info(f"warranty matches: {self.warranties}")
        log.info(f"serials: {self.serials}")
        log.info(f"{self.bill_name}, {self.bill_postcode}")
        log.info(f"{self.ship_name}, {self.ship_postcode}")
        log.info(f"{self.order_date}, {self.dispatch_date}")
