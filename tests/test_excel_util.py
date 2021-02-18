import excel_util
import pytest

@pytest.fixture(scope='module')
def workbook():
    wb = excel_util.Spreadsheet("./test_excel_util.xlsx")
    yield wb
    wb.ws.range('A5:F5').api.Delete()
    wb.save()
    wb.close()

def test_get_last_column(workbook):
    """Returns last filled in column"""
    assert workbook.get_last_column() == 'F'

def test_get_last_row(workbook):
    """Returns last filled in row"""
    assert workbook.get_last_row() == 4

def test_get_cell(workbook):
    """Returns value of the cell given row and column numbers"""
    assert workbook.get_cell(3,1) == '507906000030242007'

def test_write_data(workbook):
    """Appends a row of data to worksheet."""
    workbook.write_data("example data")
    assert workbook.get_cell(workbook.get_last_row(), 1) == "example data"
