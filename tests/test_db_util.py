import db_util
import pytest
import datetime

@pytest.fixture(scope='module')
def mydb():
    db = db_util.DB("warranty_database")
    yield db
    db.delete_from_db('ops_extended_warranty', 'order_id', 1234)
    db.delete_from_db('ops_serial_numbers', 'order_id', 1234)
    db.delete_from_db('ops_orders', 'so_id', 1234)
    db.close_db()

def test_insert_order(mydb):
    """Inserts order data. """
    order = (1234, 'so-123', '2020-10-12', '2020-10-13', 'testorder bill', 'testorder shipp', 'bb1234', 'ss1234')
    mydb.insert_order(order)

def test_insert_serials(mydb):
    """Inserts serial numbers."""
    serials = ['12345', '67890', '12368']
    mydb.insert_serials(1234, serials)

def test_insert_warranty(mydb):
    """Inserts extended warranty duration (int)."""
    warr = 2
    mydb.insert_warranty(1234, warr)

def test_check_if_in_db(mydb):
    """Given sales order number returns 0 if not found, count(1) for every find."""
    assert mydb.check_if_in_db('so-123')

def test_find(mydb):
    """Given column name and value looks for match LIKE it in whole database"""
    find = [(1234, 'so-123', datetime.date(2020, 10, 12), datetime.date(2020, 10, 13), 2)]
    assert mydb.find("ops_orders.so_number", 'so-123') == find
    assert mydb.find('ops_orders.shipping_name', 'testorder ship') == find
    assert mydb.find('ops_orders.billing_name', 'testorder bill') == find
    assert mydb.find('ops_orders.billing_postcode', 'bb1234') == find
    assert mydb.find('ops_orders.shipping_postcode', 'ss1234') == find
    assert mydb.find('ops_serial_numbers.sn', '67890') == find
    #partial match
    assert mydb.find('ops_orders.shipping_name', 'testorder') == find

def test_delete_from_db(mydb):
    """"Given table and column name deletes passed value from db."""
    order = (1111, 'so-to_delete', '2020-10-12', '2020-10-13', 'test bill', 'test shipp', 'bb1234', 'ss1234')
    mydb.insert_order(order)
    mydb.delete_from_db('ops_orders', 'so_number', 'so-to_delete')
    assert mydb.check_if_in_db('so-to_delete') == 0

def test_update_postcode(mydb):
    """Updates shipping postcode given so_id and value"""
    mydb.update_postcode(1234, 'SS1234 updated')
    assert mydb.find('ops_orders.shipping_postcode', 'SS1234 updated') == [(1234, 'so-123', datetime.date(2020, 10, 12), datetime.date(2020, 10, 13), 2)]

def test_update_addresses(mydb):
    """Updates billing and shipping addresses given so_id (names and postcodes)"""
    updated_values = ('updated billing', 'BB12 updated', 'updated shipping', 'SS12 updated again')
    mydb.update_addresses(1234, updated_values)
    assert mydb.find('ops_orders.billing_name', 'updated billing') == [(1234, 'so-123', datetime.date(2020, 10, 12), datetime.date(2020, 10, 13), 2)]

def test_find_order_by_no(mydb):
    """Returns order details given order number."""
    assert mydb.find_order_by_no('so-123') == [('so-123', datetime.date(2020, 10, 12), datetime.date(2020, 10, 13), 1234)]

def test_find_order_by_sn(mydb):
    """Returns order details given serial number of an associated device"""
    assert mydb.find_order_by_sn('12368') == [('so-123', datetime.date(2020, 10, 12), datetime.date(2020, 10, 13), 1234)]

def test_insert_sn_into_order(mydb):
    """Inserts serial number given its value and so_id"""
    mydb.insert_sn_into_order(1234, '10007')
    assert mydb.find_order_by_sn('10007') == [('so-123', datetime.date(2020, 10, 12), datetime.date(2020, 10, 13), 1234)]
