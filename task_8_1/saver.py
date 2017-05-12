import xlwt


__author__ = "Andrew Gafiychuk"


class ExcelDS(object):
    """
    Class that implement some methods to work with
    Excel file format.
    Takes Scraper data and save it in .xls file.
    
    """
    def __init__(self, file_name, sheet_name):
        """
        Constructor.
        Init some file params as file_name and sheet_name.
        Create WorkBook and Worksheet.
        
        """
        self.file = file_name
        self.sheet = sheet_name

        self.wb = xlwt.Workbook()
        self.ws = self.wb.add_sheet(self.sheet)

    def write_data(self, data_list):
        """
        Method that takes list of data from scraper and save it
        in file.

        """
        try:
            style0 = xlwt.easyxf(num_format_str='general')
            style1 = xlwt.easyxf(
                num_format_str='_("$"* #,##0.00_);'
                               '_("$"* (#,##0.00);'
                               '_("$"* "-"??_);_(@_)')
            style2 = xlwt.easyxf(num_format_str='0.00%')

            header_name = ['Name', 'Symbol', 'Market Cap',
                           'Price', 'Circulating Supply',
                           'Volume(24h)', '% 1h', '% 24h', '% 7d']

            for n, header in enumerate(header_name):
                self.ws.write(0, n, header)

            for n, record in enumerate(data_list, 1):
                self.ws.write(n, 0, record[0], style0)
                self.ws.write(n, 1, record[1], style0)
                self.ws.write(n, 2, record[2], style1)
                self.ws.write(n, 3, record[3], style1)
                self.ws.write(n, 4, record[4], style1)
                self.ws.write(n, 5, record[5], style1)
                self.ws.write(n, 6, record[6], style2)
                self.ws.write(n, 7, record[7], style2)
                self.ws.write(n, 8, record[8], style2)

            self.data_saving()

            print("[+] Data saved success !!!")

        except Exception as err:
            print("[+] Data save error...\n"
                  "{0}".format(err))

    def data_saving(self):
        """
        Save data method.
        Save changes to Work Book.

        """
        self.wb.save(self.file)
