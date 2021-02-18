import update_db
import pytest
from collections import namedtuple
from db_util import DB

@pytest.fixture(scope='module')
def mydb():
    db = DB("serialnumbers")
    yield db

    db.delete_from_db('orders', 'so_id', 1111)
    db.delete_from_db('serial_numbers', 'order_id', 2222)
    db.delete_from_db('extended_warranty', 'order_id', 2222)
    db.delete_from_db('orders', 'so_id', 2222)

    db.delete_from_db('extended_warranty', 'order_id', 9999)
    db.delete_from_db('orders', 'so_id', 9999)

    db.close_db()

def test_add_data(mydb):
    """
    Given data set
    inserts order data into db
    inserts serial numbers into db
    if that fails, deletes the order from db
    inserts extended warranty data into db when SKU found in matches, otherwise writes its data to spreadsheet
    """
    Order = namedtuple('Order', 'so_id, so_no, order_date, dispatch_date, bill_name, ship_name, bill_postcode, ship_postcode, serials, warranties')
    test_order = Order(1111, 'so-test', '2020-10-12', '2020-10-13', 'test bill', 'test shipp', 'bb12', 'ss12', None, None)
    test_order2 = Order(2222, 'so-test2', '2020-10-12', '2020-10-13', 'test bill', 'test shipp', 'bb12', 'ss12', ["sn123", "sn12345"], ['so_id', 'test warranty'])
    update_db.add_data(test_order, mydb)
    update_db.add_data(test_order2, mydb)

    assert mydb.find_order_by_no('so-test')
    assert mydb.find_order_by_no('so-test2')
    assert mydb.find_order_by_sn('sn123')

    test_incorrect_order = Order(123123, 'so-test', '2020-10-12', '2020-10-13', 'test bill', 'test shipp', 'bb12', 'ss12', 123456, None)

    with pytest.raises(Exception) as exinfo:
        update_db.add_data(test_incorrect_order, mydb)
    msg = exinfo.value.args[0]
    assert msg == "Failed to add serials for: so-test:123123"

    #sku match should not insert a data to spreadhsheet, goes straight to db
    test_warranty_with_sku = Order(9999, 'so-test', '2020-10-12', '2020-10-13', 'test bill', 'test shipp', 'bb12', 'ss12', None, ['454647', 'cca-lpq-crs-pre-8', 'something'])
    update_db.add_data(test_warranty_with_sku, mydb)

    update_db.close_spreadsheet()

    from excel_util import Spreadsheet
    wb = Spreadsheet("./extended_warranty.xlsx")
    assert wb.get_cell(wb.get_last_row(), 1) == "so_id" #that is test_order2
    wb.ws.range('A5:F5').api.Delete()
    wb.save()
    wb.close()