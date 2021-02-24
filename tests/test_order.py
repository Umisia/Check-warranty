import order
import config
import zoho_oauth
import pytest
import requests


def test_matcher():
    """
    Flag: warranty/sn
    Given flag and string
    checks if the string matches warranty/sn criteria
    """

    warr = 'Extended warranty (1 year, 3 in total ) for SO-9929', \
           'Extended Manufacturer Warranty 1 Yr', \
           'Extended 12 month warranty for the...', \
           'classcare for quarto standard set', \
           '2x Quarto GSP + 2x Q su + additional 12mth warranty'

    not_warr = 'foc warranty replacement'
    for w in warr:
        assert order.matcher(w, 'warranty') is True
    for nw in not_warr:
        assert order.matcher(nw, 'warranty') is False

    sns = 'MS123456', '250W123456', '5215w12345', '001vr3334'
    not_sn = 'ssvr'
    for sn in sns:
        assert order.matcher(sn, 'sn') is True
    for nsn in not_sn:
        assert order.matcher(nsn, 'sn') is False

def test_validate_sn():
    """Returns sn.upper() when string is a serial number, otherwise None"""
    sns = '597wtv151111', '597WTV151111', 'ms123456'
    for sn in sns:
        assert order.validate_sn(sn) == sn.upper()

    not_sns = 'ms123', '600w123'
    for n_sn in not_sns:
        assert order.validate_sn(n_sn) is None

class TestINVorder:
    @pytest.fixture(scope='class')
    def inv_token(self):
        token = config.inv_token
        yield zoho_oauth.refresh_token(token)

    def test_get_xls_content(self, inv_token, inv_filecontent_data):
        request_head = {'orgId': config.org_id, 'Authorization': 'Zoho-oauthtoken ' + inv_token}
        response = requests.get(
            "https://inventory.zoho.com/api/v1/salesorders/" + '507906000003487301' + "/documents/" + '507906000003629019', headers= request_head, stream=True)
        assert order.get_xls_content(response.content) == inv_filecontent_data['xlsx']

    def test_get_docx_content(self, inv_token, inv_filecontent_data):
        request_head = {'orgId': config.org_id, 'Authorization': 'Zoho-oauthtoken ' + inv_token}
        response = requests.get(
            "https://inventory.zoho.com/api/v1/salesorders/" + '507906000032608009' + "/documents/" + '507906000033439233',
            headers=request_head, stream=True)
        assert order.get_docx_content(response.content) == inv_filecontent_data['docx']

    def test_so_no(self, inv_token, inv_orders_data):
        """Returns order number."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.so_no == inv_orders_data['so-no']

    def test_order_date(self, inv_token, inv_orders_data):
        """Returns order create date."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.order_date == inv_orders_data['order-date']

    def test_dispatch_date(self, inv_token, inv_orders_data):
        """Returns shipment_date or package shipment_date or order_date"""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.dispatch_date == inv_orders_data['dispatch-date']

    def test_bill_name(self, inv_token, inv_orders_data):
        """Returns billing account name."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.bill_name == inv_orders_data['billing-name']

    def test_bill_postcode(self, inv_token, inv_orders_data):
        """Returns billing postcode."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.bill_postcode ==  inv_orders_data['billing-post']

    def test_ship_name(self, inv_token, inv_orders_data):
        """Returns billing name if bill_postcode and ship_postcodes are the name
        otherwise gets shipping account name, fallback to billing name"""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.ship_name == inv_orders_data['shipping-name']

    def test_ship_postcode(self, inv_token, inv_orders_data):
        """Returns shipping postcode."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.ship_postcode == inv_orders_data['shipping-post']

    def test_warranties(self, inv_token, inv_orders_data):
        """Checks if strings in
        reference, line_items, important_information custom field
        contain extended warranty matches.
        Returns a list."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.warranties == inv_orders_data['warranty']

    def test_get_ids_filenames(self, inv_token, inv_orders_data):
        """Returns dict of document_ids and file_names attached to sales order."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.get_ids_filenames() == inv_orders_data['documents']

    def test_get_file_content(self, inv_token, inv_orders_data):
        """Given doc_id and file_name
        reads byte content of a request response
        returns document content."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        assert inv_ord.get_file_content(inv_orders_data['serials-document']['file_id'], inv_orders_data['serials-document']['filename']) == inv_orders_data['serials-document']['content']

    def test_get_serials(self, inv_token, inv_orders_data):
        """Gets ids and filenames, reads file content if file name matches criteria, extracts serials."""
        inv_ord = order.InvOrder(inv_orders_data['id'], inv_token)
        inv_ord.get_serials()
        assert inv_ord.serials == inv_orders_data['serials']

class TestCRMorder:
    @pytest.fixture(scope='class')
    def crm_token(self):
        token = config.crm_token
        yield zoho_oauth.refresh_token(token)

    def test_so_no(self, crm_token, crm_orders_data):
        """Returns sales order number."""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.so_no == crm_orders_data['so-no']

    def test_order_date(self, crm_token, crm_orders_data):
        """Returns order create date."""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.order_date == crm_orders_data['order-date']

    def test_dispatch_date(self, crm_token, crm_orders_data):
        """Returns order dispatch date."""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.dispatch_date == crm_orders_data['dispatch-date']

    def test_bill_name(self, crm_token, crm_orders_data):
        """Returns billing account name from account details API request
        or from billing name field"""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.bill_name == crm_orders_data['billing_name']

    def test_bill_postcode(self, crm_token, crm_orders_data):
        """Returns billing postcode or shipping postcode from account details API request
        or from billing postcode field"""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.bill_postcode == crm_orders_data['billing_post']

    def test_ship_name(self, crm_token, crm_orders_data):
        """Returns shipping account name from account details API request
        or from shipping name field
        or billing name"""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.ship_name == crm_orders_data['shipping_name']

    def test_ship_postcode(self, crm_token, crm_orders_data):
        """Returns shipping postcode or billing postcode from account details API request
        or from shipping postcode
        or billing postcode"""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.ship_postcode == crm_orders_data['shipping_post']

    def test_warranties(self, crm_token, crm_orders_data):
        """Checks
        product_details, product_description, description, subject
        for extended warranty matches"""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        assert crm_ord.warranties == crm_orders_data['warranty']

    def test_get_serials(self, crm_token, crm_orders_data):
        """Gets value from Serial_Numbers field, validate and appends to serials list"""
        crm_ord = order.CrmOrder(crm_orders_data['id'], crm_token)
        crm_ord.get_serials()
        assert crm_ord.serials == crm_orders_data['serials']