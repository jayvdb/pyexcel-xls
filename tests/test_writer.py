import os
from pyexcel_xls.xls import XLSWriter, XLSBook
from base import PyexcelWriterBase, PyexcelHatWriterBase


class TestNativeXLWriter:
    def test_write_book(self):
        self.content = {
            "Sheet1": [[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]],
            "Sheet2": [[4, 4, 4, 4], [5, 5, 5, 5], [6, 6, 6, 6]],
            "Sheet3": [[u'X', u'Y', u'Z'], [1, 4, 7], [2, 5, 8], [3, 6, 9]]
        }
        self.testfile = "xlwriter.xls"
        writer = XLSWriter()
        writer.open(self.testfile)
        writer.write(self.content)
        writer.close()
        reader = XLSBook()
        reader.open(self.testfile)
        content = reader.read_all()
        reader.close()
        for key in content.keys():
            content[key] = list(content[key])
        assert content == self.content

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.unlink(self.testfile)


class TestXLSnCSVWriter(PyexcelWriterBase):
    def setUp(self):
        self.testfile="test.xls"
        self.testfile2="test.csv"

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.unlink(self.testfile)
        if os.path.exists(self.testfile2):
            os.unlink(self.testfile2)


class TestXLSHatWriter(PyexcelHatWriterBase):
    def setUp(self):
        self.testfile="test.xls"

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.unlink(self.testfile)
