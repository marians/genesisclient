# encoding: utf8

import suds
import logging
from lxml import etree

gc = None


class GenesisClient(object):

    def __init__(self, site, username=None, password=None):
        self.sites = {
            'DESTATIS': {
                'webservice_url': 'https://www-genesis.destatis.de/genesisWS'
            },
            'LDNRW': {
                'webservice_url': 'https://www.landesdatenbank.nrw.de/ldbnrwws'
            },
            'REGIONAL': {
                'webservice_url': 'https://www.regionalstatistik.de/genesisws'
            },
            'BAYERN': {
                'webservice_url': 'https://www.statistikdaten.bayern.de/genesisWS'
            },
            #'SACHSEN': {
            #    'webservice_url': 'http://www.statistik.sachsen.de/...'
            #},
            'BILDUNG': {
                'webservice_url': 'https://www.bildungsmonitoring.de/bildungws'
            }
        }
        self.endpoints = {
            'TestService': '/services/TestService?wsdl',
            #'RechercheService': '/services/RechercheService?wsdl',
            'RechercheService_2010': '/services/RechercheService_2010?wsdl',
            'DownloadService': '/services/DownloadService?wsdl',
            #'DownloadService_2010': '/services/DownloadService_2010?wsdl',
            #'ExportService': '/services/ExportService?wsdl',
            #'ExportService_2010': '/services/ExportService_2010?wsdl',
            #'GEOMISService': '/services/GEOMISService?wsdl',
            #'NutzerService': '/services/NutzerService?wsdl',
            #'Version': '/services/Version?wsdl',
        }
        if site is None:
            raise Exception('No site given')
        if site not in self.sites:
            sitekeys = ", ".join(sorted(self.sites.keys()))
            raise ValueError('Site not known. Use one of %s.' % sitekeys)
        self.site = site
        self.username = None
        self.password = None
        self.service_clients = {}
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password

    def init_service_client(self, name):
        """
        Initializes a client for a certain endpoint, identified by name,
        returns it and stores it internally for later re-use.
        """
        if name not in self.service_clients:
            url = (self.sites[self.site]['webservice_url']
                  + self.endpoints[name])
            self.service_clients[name] = suds.client.Client(url, retxml=True)
        return self.service_clients[name]

    def test_service(self):
        """
        Calls functions for test purposes.
        whoami and Exception handling.
        """
        client = self.init_service_client('TestService')
        client.service.whoami()
        try:
            client.service.exception()
        except suds.WebFault:
            pass

    def search(self, searchterm='*:*', limit=500, category='alle'):
        """
        Allows search for a resource (property, table, statistic, ...)
        by keyword.
        searchterm: The keyword you are trying to find in meta data
        category (defaults to any category):
            "Tabelle" for data tables,
            "Zeitreihe" for time series,
            "Datenquader", "Merkmal", "Statistik"
        """
        client = self.init_service_client('RechercheService_2010')
        #print client
        params = dict(luceneString=searchterm,
                      kennung=self.username,
                      passwort=self.password,
                      listenLaenge=str(limit),
                      sprache='de',
                      kategorie=category
                      )
        result = client.service.Recherche(**params)
        root = etree.fromstring(result)
        out = {
            'meta': {},
            'results': []
        }
        for element in root.iter("trefferUebersicht"):
            otype = element.find("objektTyp")
            num = element.find("trefferAnzahl")
            if otype is not None and num is not None:
                out['meta'][otype.text] = int(num.text)
        for element in root.iter("trefferListe"):

            code = element.find('EVAS')
            description = element.find('kurztext')
            name = element.find('name')
            if name is not None:
                name = name.text
            otype = element.find("objektTyp")
            if otype is not None:
                otype = otype.text
            if code is not None:
                out['results'].append({
                    'id': code.text,
                    'type': otype,
                    'name': name,
                    'description': clean(description.text)
                })
        return out

    def terms(self, filter='*', limit=20):
        """
        Gives access to all terms which can be used for search. Example:
        filter='bev*' will return only terms starting with "bev". Can be used
        to implement search term auto-completion.
        """
        client = self.init_service_client('RechercheService_2010')
        #print client
        params = dict(kennung=self.username,
                      passwort=self.password,
                      filter=filter,
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.BegriffeKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("begriffeKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def properties(self, filter='*', criteria='Code', type="alle", limit=500):
        """
        Access to the properties catalogue (data attributes).
        filter:
            Selection string, supporting asterisk notation.
        criteria:
            Can be "Code" or "Inhalt", defines on what the filter parameter
            matches and what the result is sorted by.
        type:
            Type of the properties to be matched. Supported are:
            "klassifizierend"
            "insgesamt"
            "räumlich"
            "sachlich"
            "wert"
            "zeitlich"
            "zeitidentifizierend"
            "alle" (default)
        area
        """
        client = self.init_service_client('RechercheService_2010')
        #print client
        params = dict(kennung=self.username,
                      passwort=self.password,
                      filter=filter,
                      kriterium=criteria,
                      typ=type,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.MerkmalsKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("merkmalsKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def property_occurrences(self, property_code, selection='*',
                             criteria="Code", limit=500):
        """
        Retrieve occurences of properties. Use property_code to indicate the
        property. You can further narrow down the selection of occurences
        using the selection parameter which supports asterisk notation
        (e.g. selection='hs18*').
        """
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=property_code,
                      auswahl=selection,
                      kriterium=criteria,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.MerkmalAuspraegungenKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("merkmalAuspraegungenKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def property_data(self, property_code='*', selection='*',
                             criteria="Code", limit=500):
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=property_code,
                      auswahl=selection,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.MerkmalDatenKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("merkmalDatenKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            beschriftungstext = element.find('beschriftungstext')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text),
                    'longdescription': clean(beschriftungstext.text)
                })
        return out

    def property_statistics(self, property_code='*', selection='*',
                             criteria="Code", limit=500):
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=property_code,
                      auswahl=selection,
                      kriterium=criteria,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.MerkmalStatistikenKatalog(**params)
        print result

    def property_tables(self, property_code='*', selection='*', limit=500):
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=property_code,
                      auswahl=selection,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.MerkmalTabellenKatalog(**params)
        print result

    def statistics(self, filter='*', criteria='Code', limit=500):
        """
        Load information on statistics
        """
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      filter=filter,
                      kriterium=criteria,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.StatistikKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("statistikKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def statistic_data(self, statistic_code='*', selection='*', limit=500):
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=statistic_code,
                      auswahl=selection,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.StatistikDatenKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("statistikDatenKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            beschriftungstext = element.find('beschriftungstext')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text),
                    'longdescription': clean(beschriftungstext.text)
                })
        return out

    def statistic_properties(self, statistic_code='*', criteria='Code', selection='*', limit=500):
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=statistic_code,
                      auswahl=selection,
                      kriterium=criteria,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.StatistikMerkmaleKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("statistikMerkmaleKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def statistic_tables(self, statistic_code='*', selection='*', limit=500):
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=statistic_code,
                      auswahl=selection,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.StatistikTabellenKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("statistikTabellenKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def tables(self, filter='*', limit=500):
        """
        Retrieve information on tables
        """
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      filter=filter,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de')
        result = client.service.TabellenKatalog(**params)
        root = etree.fromstring(result)
        out = []
        for element in root.iter("tabellenKatalogEintraege"):
            code = element.find('code')
            inhalt = element.find('inhalt')
            if code is not None:
                out.append({
                    'id': code.text,
                    'description': clean(inhalt.text)
                })
        return out

    def catalogue(self, filter='*', limit=500):
        """
        Retrieve metadata on data offerings. Can be filtered by code, e.g.
        filter='11111*' delivers all entries with codes starting with '11111'.
        """
        client = self.init_service_client('RechercheService_2010')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      filter=filter,
                      bereich='Alle',
                      listenLaenge=str(limit),
                      sprache='de'
                      )
        result = client.service.DatenKatalog(**params)
        return result

    def table_export(self, table_code,
            regionalschluessel='',
            format='csv'):
        """
        Return data for a given table
        """
        client = self.init_service_client('DownloadService')
        params = dict(kennung=self.username,
                      passwort=self.password,
                      name=table_code,
                      bereich='Alle',
                      format=format,
                      komprimierung=False,
                      startjahr='1900',
                      endjahr='2100',
                      zeitscheiben='',
                      regionalschluessel=regionalschluessel,
                      sachmerkmal='',
                      sachschluessel='',
                      sprache='de',
                      )
        result = None
        if format == 'xls':
            del params['format']
            result = client.service.ExcelDownload(**params)
            # Really nasty way to treat a multipart message...
            # (room for improvement)
            parts = result.split("\r\n")
            for i in range(0, 12):
                parts.pop(0)
            parts.pop()
            parts.pop()
            return "\r\n".join(parts)
        else:
            result = client.service.TabellenDownload(**params)
            parts = result.split(result.split("\r\n")[1])
            data = parts[2].split("\r\n\r\n", 1)[-1]
            #data = unicode(data.decode('latin-1'))
            #data = unicode(data.decode('utf-8'))
            return data


def clean(s):
    """Clean up a string"""
    if s is None:
        return None
    s = s.replace("\n", " ")
    s = s.replace("  ", " ")
    s = s.strip()
    return s


def download(client, args):
    """
    Issue a download from command line arguments
    """
    rs = '*'
    path = '%s.%s' % (args.download, args.format)
    if args.regionalschluessel is not None and args.regionalschluessel != '*':
        rs = args.regionalschluessel
        path = '%s_%s.%s' % (args.download, args.regionalschluessel, args.format)
    print "Downloading to file %s" % path
    result = client.table_export(args.download,
            regionalschluessel=rs,
            format=args.format)
    open(path, 'wb').write(result)


def search(client, args):
    """
    Search the catalog for a term
    using options given via the command line
    """
    term = args.searchterm
    if type(term) != unicode:
        term = term.decode('utf8')
    result = client.search(term)
    for cat in result['meta'].keys():
        if result['meta'][cat] > 0:
            print "Hits of type '%s': %d" % (cat.upper(), result['meta'][cat])
    for hit in result['results']:
        otype = hit['type'].upper()
        if otype == 'MERKMAL' or otype == 'STATISTIK':
            print "%s %s %s" % (otype, clean(hit['name']), clean(hit['description']))
        elif otype == 'TABELLE':
            print "%s %s %s" % (otype, clean(hit['name']), clean(hit['description']))
        elif otype == 'BEGRIFF':
            print "%s %s" % (otype, clean(hit['name']))
        else:
            print "%s %s" % (hit['type'].upper(), hit)


def lookup(client, args):
    """
    Lookup tables and print out info on found entries
    """
    term = args.lookup
    if type(term) != unicode:
        term = term.decode('utf8')
    for stat in gc.statistics(filter=term):
        print "STATISTIC: %s %s" % (stat['id'], stat['description'])
    for s in gc.statistic_data(statistic_code=term):
        print "STATISTIC DATA: %s %s" % (s['id'], s['description'])
    for s in gc.statistic_properties(statistic_code=term):
        print "STATISTIC PROPERTY: %s %s" % (s['id'], s['description'])
    for s in gc.statistic_tables(statistic_code=term):
        print "STATISTIC TABLE: %s %s" % (s['id'], s['description'])
    for prop in gc.properties(filter=term):
        print "PROPERTY: %s %s" % (prop['id'], prop['description'])
    if '*' not in term:
        for prop in gc.property_occurrences(property_code=term):
            print "PROPERTY OCCURRENCE: %s %s" % (prop['id'], prop['description'])
    for prop in gc.property_data(property_code=term):
        print "PROPERTY DATA: %s %s" % (prop['id'], prop['longdescription'])
    for table in gc.tables(filter=term):
        print "TABLE: %s %s" % (table['id'], table['description'])
    for term in gc.terms(filter=term):
        print "TERM: %s %s" % (term['id'], term['description'])


def main():
    #logging.basicConfig(level='DEBUG')
    logging.basicConfig(level='WARN')
    # Our command-line options
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='These are todays options:')
    parser.add_argument('-s', dest='site', default=None,
                   help='Genesis site to connect to (DESTATIS or LDNRW)')
    parser.add_argument('-u', dest='username', default='',
                   help='username for Genesis login')
    parser.add_argument('-p', dest='password', default='',
                   help='username for Genesis login')
    parser.add_argument('-l', '--lookup', dest='lookup', default=None,
                   metavar="FILTER",
                   help='Get information on the table, property etc. with the key named FILTER. * works as wild card.')
    parser.add_argument('-g', '--search', dest='searchterm', default=None,
                   metavar="SEARCHTERM",
                   help='Find an item using an actual search engine. Should accept Lucene syntax.')
    parser.add_argument('-d', '--downlaod', dest='download', default=None,
                   metavar="TABLE_ID",
                   help='Download table with the ID TABLE_ID')
    parser.add_argument('--rs', dest='regionalschluessel', default=None,
                   metavar="RS", help='Only select data for region key RS')
    parser.add_argument('-f', '--format', dest='format', default='csv',
                   metavar="FORMAT", help='Download data in this format (csv, html, xls). Default ist csv.')

    args = parser.parse_args()

    # create the webservice client
    gc = GenesisClient(args.site, username=args.username,
                    password=args.password)
    # test if the service works
    #gc.test_service()

    if args.download is not None:
        download(gc, args)
    elif args.searchterm is not None:
        search(gc, args)
    elif args.lookup is not None:
        lookup(gc, args)

    # See? All I allow you to do is download stuff.
    sys.exit()

    # submit a search
    result = gc.search('schule', limit=10, category='Tabelle')
    counter = 0
    for item in result:
        #print counter, item.name, item.objektTyp, item.kurztext
        counter += 1

    # retrieve terms satrting with 'a'.
    terms = gc.terms(filter='a*')
    print "Terms list has", len(terms), "entries. Example:"
    print (terms[0].inhalt)

    # retrieve catalogue items starting with "11111"
    catalogue = gc.catalogue(filter='11111*')
    print "Catalogue result has", len(catalogue), "entries. Example:"
    print (catalogue[0].code,
           catalogue[0].beschriftungstext.replace("\n", " "),
           catalogue[0].inhalt)

    # retrieve properties
    properties = gc.properties(filter='B*', type='sachlich')
    print "Properties list has", len(properties), "entries. Example:"
    print (properties[0].code, properties[0].inhalt)

    # retrieve occurences for a property
    occurences = gc.property_occurrences(property_code=properties[0].code)
    print "Occurrences list has", len(occurences), "entries. Example:"
    print (occurences[0].code, occurences[0].inhalt)

    # retrieve data for a property
    data = gc.property_data(property_code=properties[0].code)
    print "Data list has", len(data), "entries. Example:"
    print (data[0].code,
           data[0].inhalt,
           data[0].beschriftungstext.replace("\n", " "))

    statistics = gc.property_statistics(property_code=properties[0].code)
    print "Statistics list has", len(statistics), "entries. Example:"
    print (statistics[0].code,
           statistics[0].inhalt.replace("\n", " "))

    tables = gc.property_tables(property_code=properties[0].code)
    print "Tables list has", len(statistics), "entries. Example:"
    print (tables[0].code,
           tables[0].inhalt.replace("\n", " "))

    table = gc.table_export(table_code=tables[0].code)
    print table

if __name__ == '__main__':
    main()
