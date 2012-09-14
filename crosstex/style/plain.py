import math

import crosstex.style


class Style(crosstex.style.Style):

    @classmethod
    def formats(cls):
        return set(['bbl'])

    def __init__(self, flags=None, titlephrases=None, titlesmalls=None):
        self._titlephrases = titlephrases or set([])
        self._titlesmalls = titlesmalls or set([])
        self._flags = flags or set([])

    def sort_key(self, citation, fields=None):
        if fields is not None: # XXX
            raise NotImplementedError()
        cite, obj = citation
        author = None
        if 'author' in obj.allowed and obj.author:
            author = [a.name.value if hasattr(a, 'name') else a.value for a in obj.author]
            author = [crosstex.style.name_sort_last_first(a) for a in author]
            author = tuple(author)
        title = None
        if 'title' in obj.allowed and obj.title:
            title = obj.title.value
        where = None
        if 'booktitle' in obj.allowed and obj.booktitle:
            where = self.render_booktitle(obj.booktitle)
        elif 'journal' in obj.allowed and obj.journal:
            where = self.render_journal(obj.journal)
        when = None
        if 'year' in obj.allowed and obj.year:
            when = str(obj.year.value)
        return author, title, where, when

    def render(self, citations):
        num = int(math.log10(len(citations))) + 1 if citations else 1
        bib  = '\\newcommand{\etalchar}[1]{$^{#1}$}\n'
        bib += '\\begin{thebibliography}{%s}\n' % ('0' * num)
        for cite, obj in citations:
            cb = self._callback(obj.kind)
            if cb is None:
                raise crosstex.style.UnsupportedCitation(obj.kind)
            item = cb(obj)
            bib += '\n' + self.bibitem(cite, item)
        bib += '\n\end{thebibliography}\n'
        return bib

    # Stuff to override for other formats

    def bibitem(self, cite, item):
        return ('\\bibitem{%s}\n' % cite) + item + '\n'

    def emph(self, text):
        return r'\emph{' + text.strip() + '}'

    def block(self, text):
        return text.strip()

    def block_sep(self):
        return '\n\\newblock '

    # Stuff for rendering

    def render_str(self, string, which):
        if isinstance(string, crosstex.parse.Value):
            string = str(string.value)
        elif 'short-' + which in self._flags:
            string = str(string.shortname.value)
        elif 'short-' + which not in self._flags:
            string = str(string.longname.value)
        return string

    def render_author(self, author, context=None, history=None):
        author  = [a.name.value if hasattr(a, 'name') else a.value for a in author]
        if 'short-author' in self._flags:
            author  = crosstex.style.names_shortfirst_last(author)
        else:
            author  = crosstex.style.names_first_last(author)
        author  = crosstex.style.list_comma_and(author)
        return author

    def render_title(self, title, context=None, history=None):
        title = title.value
        if 'titlecase-default' in self._flags:
            return title
        elif 'titlecase-upper' in self._flags:
            return crosstex.style.title_uppercase(title)
        elif 'titlecase-title' in self._flags:
            return crosstex.style.title_titlecase(title, self._titlephrases)
        elif 'titlecase-lower' in self._flags:
            return crosstex.style.title_lowercase(title, self._titlesmalls)
        return title

    def render_booktitle(self, booktitle, context=None, history=None):
        if isinstance(booktitle, crosstex.objects.workshop):
            return self.render_str(booktitle, 'workshop')
        elif isinstance(booktitle, crosstex.objects.conference):
            return self.render_str(booktitle, 'conference')
        elif isinstnace(booktitle, crosstex.parse.Value):
            return self.render_str(booktitle, 'booktitle')

    def render_journal(self, journal, context=None, history=None):
        return self.render_str(journal, 'journal')

    def render_pages(self, pages, context=None, history=None):
        pages = str(pages)
        if '-' in pages:
            return 'pages %s' % pages
        else:
            return 'page %s' % pages

    def render_address(self, address, context=None, history=None):
        city, state, country = None, None, None
        if isinstance(address, crosstex.objects.location):
            if address.city:
                city = self.render_str(address.city, 'city')
            if address.state:
                state = self.render_str(address.state, 'state')
            if address.country:
                country = self.render_str(address.country, 'country')
        elif isinstance(address, crosstex.objects.country):
            country = self.render_str(address, 'country')
        elif isinstance(address, crosstex.objects.state):
            state = self.render_str(address, 'state')
            if address.country:
                country = self.render_str(address.country, 'country')
        elif isinstance(address, crosstex.parse.Value):
            return self.render_str(address, 'address')
        return ', '.join([x for x in (city, state, country) if x is not None])

    def render_year(self, year, context=None, history=None):
        if isinstance(year, crosstex.parse.Value):
            return self.render_str(year, 'year')

    def render_month(self, month, context=None, history=None):
        return self.render_str(month, 'month')

    def render_article(self, article, context=None, history=None):
        author  = self.render_author(article.author)
        title   = self.render_title(article.title)
        journal = self.render_journal(article.journal)
        year    = self.render_year(article.year) 
        volume  = str(article.volume.value) if article.volume else None
        number  = str(article.number.value) if article.number else None
        pages   = str(article.pages.value) if article.pages else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self.block(crosstex.style.punctuate(author, '.', ''))
        if title:
            second = self.block(crosstex.style.punctuate(title, '.', ''))
        if journal:
            if 'add-in' in self._flags:
                third += 'In '
            third += self.emph(journal)
        volnumpages = ''
        if number or volume or pages:
            if volume:
                volnumpages += str(volume)
            if number:
                volnumpages += '(%s)' % number
            if pages:
                if volume or number:
                    volnumpages += ':%s' % pages
                else:
                    volnumpages += self.render_pages(pages)
        if volnumpages:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += volnumpages
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self.block(third)
        return self.block_sep().join([b for b in (first, second, third) if b])

    def render_book(self, book, context=None, history=None):
        author    = self.render_author(book.author)
        # XXX need to handle editors
        title     = self.render_title(book.title)
        publisher = self.render_str(book.publisher, 'publisher') if book.publisher else None
        address   = self.render_address(book.address) if book.address else None
        year      = self.render_year(book.year) if book.year else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self.block(crosstex.style.punctuate(author, '.', ''))
        if title:
            second = self.block(crosstex.style.punctuate(title, '.', ''))
        if publisher:
            third = publisher
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self.block(third)
        return self.block_sep().join([b for b in (first, second, third) if b])

    def render_inproceedings(self, inproceedings, context=None, history=None):
        author    = self.render_author(inproceedings.author)
        title     = self.render_title(inproceedings.title)
        booktitle = self.render_booktitle(inproceedings.booktitle)
        pages     = self.render_pages(inproceedings.pages.value) if inproceedings.pages else None
        address   = self.render_address(inproceedings.address) if inproceedings.address else None
        year      = self.render_year(inproceedings.year) if inproceedings.year else None
        month     = self.render_month(inproceedings.month) if inproceedings.month else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self.block(crosstex.style.punctuate(author, '.', ''))
        if title:
            second = self.block(crosstex.style.punctuate(title, '.', ''))
        if booktitle:
            if 'add-in' in self._flags:
                third += 'In '
            if 'add-proceedings' in self._flags:
                third += 'Proceedings of the '
            elif 'add-proc' in self._flags:
                third += 'Proc. of '
            third += crosstex.style.punctuate(self.emph(booktitle), ',', ' ')
        if pages:
            third = crosstex.style.punctuate(third, ',', ' ') + pages
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if month and year:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += month + ' ' + year
        elif year:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += year
        third = crosstex.style.punctuate(third, '.', '')
        third = self.block(third)
        return self.block_sep().join([b for b in (first, second, third) if b])

    def render_misc(self, misc, context=None, history=None):
        author    = self.render_author(misc.author) if misc.author else None
        title     = self.render_title(misc.title) if misc.title else None
        howpub    = str(misc.howpublished.value) if misc.howpublished else None
        booktitle = self.render_booktitle(misc.booktitle) if misc.booktitle else None
        address   = self.render_address(misc.address) if misc.address else None
        year      = self.render_year(misc.year) if misc.year else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self.block(crosstex.style.punctuate(author, '.', ''))
        if title:
            second = self.block(crosstex.style.punctuate(title, '.', ''))
        if howpub:
            third += howpub
        if booktitle:
            third = crosstex.style.punctuate(third, ',', ' ') + self.emph(booktitle)
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self.block(third)
        return self.block_sep().join([b for b in (first, second, third) if b])

    def render_techreport(self, techreport, context=None, history=None):
        author  = self.render_author(techreport.author)
        title   = self.render_title(techreport.title)
        number  = str(techreport.number.value) if techreport.number else None
        insti   = str(techreport.institution.value) if techreport.institution else None
        address = self.render_address(techreport.address) if techreport.address else None
        year    = self.render_year(techreport.year) 
        month   = self.render_month(techreport.month) if techreport.month else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self.block(crosstex.style.punctuate(author, '.', ''))
        if title:
            second = self.block(crosstex.style.punctuate(title, '.', ''))
        if insti:
            third = insti
        if address:
            third = crosstex.style.punctuate(third, ',', ' ') + address
        if number:
            third = crosstex.style.punctuate(third, ',', ' ')
            third += 'Technical Report ' +  number
        if year:
            third = crosstex.style.punctuate(third, ',', ' ') + year
        third = crosstex.style.punctuate(third, '.', '')
        third = self.block(third)
        return self.block_sep().join([b for b in (first, second, third) if b])

    def render_url(self, url, context=None, history=None):
        author = self.render_author(url.author) if url.author else None
        title  = self.render_title(url.title) if url.title else None
        link   = str(url.url.value)
        month  = self.render_month(url.accessmonth) if url.accessmonth else None
        day    = self.render_str(url.accessday, 'day') if url.accessday else None
        year   = self.render_year(url.accessyear) if url.accessyear else None
        first = ''
        second = ''
        third = ''
        if author:
            first = self.block(crosstex.style.punctuate(author, '.', ''))
        if title:
            second = self.block(crosstex.style.punctuate(title, '.', ''))
        if url:
            third = link
        if month and day and year:
            third = self.block(crosstex.style.punctuate(third, '.', ''))
            third += 'Accessed ' + month + ' ' + day + ', ' + year
        third = self.block(crosstex.style.punctuate(third, '.', ''))
        third = self.block(third)
        return self.block_sep().join([b for b in (first, second, third) if b])
