# xbsearch

Search a list of words on DuckDuckGo and gather unique domains from the results pages.

```
$ xbgog.py -h

usage: xbgog.py [-h] -f FILE [-o OUTPUT] [-v] [-d DORK] [-p PAGES]
```

**options:**

```
  -h, --help            show this help message and exit

  -f FILE, --file FILE  Path to a file containing a list of words (one per line).
  
  -o OUTPUT, --output OUTPUT
                        Path to the output file to save unique domains. Defaults to xb_DDMMYYHHMM.txt if not specified.
  
  -v, --verbose         Show detailed search information for each word (off by default).
  
  -d DORK, --dork DORK  A DuckDuckGo dork to append to each search query (e.g., 'site:*.com').
  
  -p PAGES, --pages PAGES
                        The number of search result pages to retrieve (default: 3, each page has ~10 results).
```

**Examples: **

```
python3 xbgog.py -f words.txt python3 xbgog.py -f words.txt -p 10 python3 xbgog.py -f words.txt -o mydomains.txt -d "site:*.net"
```
