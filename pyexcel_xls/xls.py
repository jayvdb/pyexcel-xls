"""
    pyexcel_xls
    ~~~~~~~~~~~~~~~~~~~

    The lower level xls/xlsm file format handler using xlrd/xlwt

    :copyright: (c) 2015-2016 by Onni Software Ltd
    :license: New BSD License
"""
import sys
import math
import datetime
import xlrd
from xlwt import Workbook, XFStyle

from pyexcel_io.book import BookReader, BookWriter
from pyexcel_io.sheet import SheetReader, SheetWriter

PY2 = sys.version_info[0] == 2
if PY2 and sys.version_info[1] < 7:
    from ordereddict import OrderedDict
else:
    from collections import OrderedDict


DEFAULT_DATE_FORMAT = "DD/MM/YY"
DEFAULT_TIME_FORMAT = "HH:MM:SS"
DEFAULT_DATETIME_FORMAT = "%s %s" % (DEFAULT_DATE_FORMAT, DEFAULT_TIME_FORMAT)


def is_integer_ok_for_xl_float(value):
    if value == math.floor(value):
        return True
    else:
        return False


def xldate_to_python_date(value):
    """
    convert xl date to python date
    """
    date_tuple = xlrd.xldate_as_tuple(value, 0)
    ret = None
    if date_tuple == (0, 0, 0, 0, 0, 0):
        ret = datetime.datetime(1900, 1, 1, 0, 0, 0)
    elif date_tuple[0:3] == (0, 0, 0):
        ret = datetime.time(date_tuple[3],
                            date_tuple[4],
                            date_tuple[5])
    elif date_tuple[3:6] == (0, 0, 0):
        ret = datetime.date(date_tuple[0],
                            date_tuple[1],
                            date_tuple[2])
    else:
        ret = datetime.datetime(
            date_tuple[0],
            date_tuple[1],
            date_tuple[2],
            date_tuple[3],
            date_tuple[4],
            date_tuple[5]
        )
    return ret


class XLSheet(SheetReader):
    """
    xls sheet

    Currently only support first sheet in the file
    """
    def __init__(self, sheet, auto_detect_int=True, **keywords):
        SheetReader.__init__(self, sheet, **keywords)
        self.auto_detect_int = auto_detect_int
    
    def number_of_rows(self):
        """
        Number of rows in the xls sheet
        """
        return self.native_sheet.nrows

    def number_of_columns(self):
        """
        Number of columns in the xls sheet
        """
        return self.native_sheet.ncols

    def cell_value(self, row, column):
        """
        Random access to the xls cells
        """
        cell_type = self.native_sheet.cell_type(row, column)
        value = self.native_sheet.cell_value(row, column)
        if cell_type == xlrd.XL_CELL_DATE:
            value = xldate_to_python_date(value)
        elif cell_type == xlrd.XL_CELL_NUMBER and self.auto_detect_int:
            if is_integer_ok_for_xl_float(value):
                value = int(value)
        return value

    def to_array(self):
        for r in range(0, self.number_of_rows()):
            row = []
            tmp_row = []
            for c in range(0, self.number_of_columns()):
                cell_value = self.cell_value(r, c)
                tmp_row.append(cell_value)
                if cell_value is not None and cell_value != '':
                    row += tmp_row
                    tmp_row = []
            yield row


class XLSBook(BookReader):
    """
    XLSBook reader

    It reads xls, xlsm, xlsx work book
    """
    def __init__(self):
        BookReader.__init__(self)
        self.book = None
        self.file_content = None

    def open(self, file_name, **keywords):
        BookReader.open(self, file_name, **keywords)

    def open_stream(self, file_stream, **keywords):
        BookReader.open_stream(self, file_stream, **keywords)

    def open_content(self, file_content, **keywords):
        self.keywords = keywords
        self.file_content = file_content

    def close(self):
        if self.book:
            self.book.release_resources()

    def read_sheet_by_index(self, sheet_index):
        self.book = self._get_book(on_demand=True)
        sheet = self.book.sheet_by_index(sheet_index)
        xlsheet = XLSheet(sheet, **self.keywords)
        return {sheet.name: xlsheet.to_array()}

    def read_sheet_by_name(self, sheet_name):
        self.book = self._get_book(on_demand=True)
        try:
            sheet = self.book.sheet_by_name(sheet_name)
        except xlrd.XLRDError as e:
            print(e)
            raise ValueError("%s cannot be found" % sheet_name)
        xlsheet = XLSheet(sheet)
        return {sheet.name: xlsheet.to_array()}

    def read_all(self):
        result = OrderedDict()
        self.book = self._get_book()
        for sheet in self.book.sheets():
            xlsheet = XLSheet(sheet, **self.keywords)
            result[sheet.name] = xlsheet.to_array()
        return result

    def _get_book(self, on_demand=False):
        if self.file_name:
            xls_book = xlrd.open_workbook(self.file_name, on_demand=on_demand)
        elif self.file_stream:
            xls_book = xlrd.open_workbook(
                None,
                file_contents=self.file_stream.getvalue(),
                on_demand=on_demand
            )
        elif self.file_content:
            xls_book = xlrd.open_workbook(
                None,
                file_contents=self.file_content,
                on_demand=on_demand
            )
        return xls_book


class XLSheetWriter(SheetWriter):
    """
    xls, xlsx and xlsm sheet writer
    """
    def set_sheet_name(self, name):
        """Create a sheet
        """
        self.native_sheet = self.native_book.add_sheet(name)
        self.current_row = 0

    def write_row(self, array):
        """
        write a row into the file
        """
        for i in range(0, len(array)):
            value = array[i]
            style = None
            tmp_array = []
            if isinstance(value, datetime.datetime):
                tmp_array = [
                    value.year, value.month, value.day,
                    value.hour, value.minute, value.second
                ]
                value = xlrd.xldate.xldate_from_datetime_tuple(tmp_array, 0)
                style = XFStyle()
                style.num_format_str = DEFAULT_DATETIME_FORMAT
            elif isinstance(value, datetime.date):
                tmp_array = [value.year, value.month, value.day]
                value = xlrd.xldate.xldate_from_date_tuple(tmp_array, 0)
                style = XFStyle()
                style.num_format_str = DEFAULT_DATE_FORMAT
            elif isinstance(value, datetime.time):
                tmp_array = [value.hour, value.minute, value.second]
                value = xlrd.xldate.xldate_from_time_tuple(tmp_array)
                style = XFStyle()
                style.num_format_str = DEFAULT_TIME_FORMAT
            if style:
                self.native_sheet.write(self.current_row, i, value, style)
            else:
                self.native_sheet.write(self.current_row, i, value)
        self.current_row += 1


class XLSWriter(BookWriter):
    """
    xls, xlsx and xlsm writer
    """
    def __init__(self):
        BookWriter.__init__(self)
        self.work_book = None

    def open(self, file_name,
             encoding='ascii', style_compression=2, **keywords):
        BookWriter.open(self, file_name, **keywords)
        self.work_book = Workbook(style_compression=style_compression,
                           encoding=encoding)

    def create_sheet(self, name):
        return XLSheetWriter(self.work_book, None, name)

    def close(self):
        """
        This call actually save the file
        """
        self.work_book.save(self.file_alike_object)


_xls_reader_registry = {
    "file_type": "xls",
    "reader": XLSBook,
    "stream_type": "binary",
    "mime_type": "application/vnd.ms-excel",
    "library": "xlrd"
}

_xls_writer_registry = {
    "file_type": "xls",
    "writer": XLSWriter,
    "stream_type": "binary",
    "mime_type": "application/vnd.ms-excel",
    "library": "xlwt-future"
}

_xlsm_registry = {
    "file_type": "xlsm",
    "reader": XLSBook,
    "stream_type": "binary",
    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "library": "xlrd"
}

_xlsx_registry = {
    "file_type": "xlsx",
    "reader": XLSBook,
    "stream_type": "binary",
    "mime_type": "application/vnd.ms-excel.sheet.macroenabled.12",
    "library": "xlrd"
}

exports = (_xls_reader_registry, _xls_writer_registry,
           _xlsm_registry, _xlsx_registry)
