import xlwings as xw
from logger import Logger

class Spreadsheet:
    def __init__(self, wb_path):
        self.wb = xw.Book(wb_path)
        self.ws = self.wb.sheets["Sheet1"]
        log.info(f"connected to {wb_path}")

    # last column filled in
    def get_last_column(self):
        return self.ws.range(1, 1).end('right').get_address(0, 0)[0]

    #last row filled in
    def get_last_row(self):
        return self.ws.range('A' + str(self.ws.cells.last_cell.row)).end('up').row

    def write_data(self,data):
        self.ws.cells(self.get_last_row()+1, 1).value = data
        log.debug(f"(written: {data} to {self.get_last_row()+1}, 1")
        
    def get_cell(self, row, col):
        return self.ws.cells(row, col).value

    def save(self):
        self.wb.save()

    def close(self):
        self.wb.close()

log = Logger(__name__).logger  
