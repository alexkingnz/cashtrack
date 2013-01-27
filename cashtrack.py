import csv
import datetime
import dateutil.parser
import fractions

DEFAULT_CATEGORIES = ["Food", "Housing", "Insurance", "Utilities", "Transport"]
DEFAULT_PEOPLE = ['Family', 'Jane', 'John', 'State']
DEFAULT_ACCOUNTS = ['Main']
DATEFMT = "%d-%b-%Y"

class NotEnoughError(ValueError):
    pass

class Money(fractions.Fraction):
    def __repr__(self):
        return '%5.2f' % self

class TransactionList(list):
    def __init__(self):
        self.category = []
        self.person = []
        self.account = []
        self.get_outstanding = Money(0)
        self.spend_outstanding = Money(0)
        self.saved_index = 0
        self.balance = {}

    def use_file(self, filename):
        self.filename = filename
        try:
            reader = csv.reader(open(self.filename,"rb"))
            fromfile = True
        except IOError:
            self.do_date(datetime.datetime.now().strftime(DATEFMT))
            for block, list in [('category', DEFAULT_CATEGORIES),
                                ('person', DEFAULT_PEOPLE),
                                ('account', DEFAULT_ACCOUNTS)]:
                for item in list:
                    self.do_new(block, item)
                self.do_default(block, list[0])
            reader = []
            fromfile = False
        for line in reader:
            getattr(self, "do_%s" % line[0])(*line[1:])
        if fromfile:
            self.saved_index=len(self)

    def save_file(self):
        tosave=self[self.saved_index:]
        if tosave:
            csv.writer(open(self.filename, "ab")).writerows(tosave)

    def precmd(line):
        if self.get_outstanding:
            if not line.split()[0]=="to":
                self.do_to(self.get_outstanding)
        if self.spend_outstanding:
            if not line.split()[0]=="from":
                self.do_from(self.spend_outstanding)
        return line

    def do_new(self, item, name):
        getattr(self, item).append(name)
        self.append(("new", item, name))

    def do_default(self, item, name):
        setattr(self, "default_%s" % item, name)
        self.append(("default", item, name))

    def do_date(self, date):
        self.date = dateutil.parser.parse(date).date()
        self.append(("date", self.date.strftime(DATEFMT)))

    def do_get(self, amount, account=None, person=None):
        if not person:
            person = self.default_person
        if not account:
            account = self.default_account
        amt = Money(amount)
        self.append(("get", amt, account, person))
        self.get_outstanding = amt

    def do_to(self, amount, category=None):
        if not category:
            category = self.default_category
        amt = Money(amount)
        if amt > self.get_outstanding:
            raise NotEnoughError
        self.append(("to", amt, category))
        self.get_outstanding -= amt

    def do_spend(self, amount, account=None):
        if not account:
            account = self.default_account
        amt = Money(amount)
        self.append(("spend", amt, account))
        self.spend_outstanding = amt

    def do_from(self, amount, category=None, person=None):
        if not category:
            category = self.default_category
        if not person:
            person = self.default_person
        amt = Money(amount)
        if amt > self.spend_outstanding:
            raise NotEnoughError
        self.append(("from", amt, category, person))
        self.spend_outstanding -= amt

if __name__=="__main__":
   transaction_list = TransactionList()
   transaction_list.use_file("cashtrack.csv")
   transaction_list.save_file()
