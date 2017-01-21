#import the libraries we'll need
import re
import scraperwiki
import urllib2
import lxml.etree
import lxml.html
import requests

# Read in a page
url = "https://reports.ofsted.gov.uk/provider/files/2631211/urn/103980.pdf"

def scrapepdf(url):
  pdfdata = urllib2.urlopen(url).read()
  print "The pdf file has %d bytes" % len(pdfdata)

  xmldata = scraperwiki.pdftoxml(pdfdata)
  print "After converting to xml it has %d bytes" % len(xmldata)
  print "The first 2000 characters are: ", xmldata[:2000]


  # turn 'xmldata' into an lxml object called 'pdfroot'
  pdfroot = lxml.etree.fromstring(xmldata)
  #find all <text> tags and put in list variable 'lines'
  lines = pdfroot.findall('.//text')
  # create new 'linenummber' variable, set at 0
  linenumber = 0
  # create empty dictionary object which we'll fill with data as we go, then store
  record = {}

  #school name is in <text top="148" left="85" width="443" height="40" font="4">
  #We try to identify lines with font="4"
  schoolname = pdfroot.findall('.//text[@font="4"]')
  for name in schoolname:
    #sometimes we get an AttributeError so we use try here to stop it breaking the whole thing
    try:
    #This line tests how many matches we get
      print 'SCHOOL NAME? ', name.text.encode('ascii', 'ignore')
  #There's only one when tested, so let's store the first and only match
  #see https://docs.python.org/2/howto/unicode.html for more on .encode('ascii', 'xmlcharrefreplace')
      record['schoolname'] = schoolname[0].text.encode('ascii', 'xmlcharrefreplace')
    except AttributeError:
      print 'AttributeError - ignored'

  #Now the date, which is in <text top="224" left="661" width="147" height="18" font="2"
  #We could look for TWO attributes using './/text[@top="224" and font="2"]' but this generates an error in lxml
  #So we might find another way to test either criteria
  dateinspected = pdfroot.findall('.//text[@top="224"]')
#  dateinspected2 = pdfroot.findall('.//text[@font="2"]')
  for i in dateinspected:
    print i.attrib.get('font')
    if i.attrib.get('font') == "2" and i is not None:
      print 'DATE MATCH on FONT? ', i.text.encode('ascii','ignore')
      record['date'] = i.text.encode('ascii','ignore')

  #loop through each item in 'lines'
  for line in lines:
    linenumber = linenumber+1
    #we are not interested in lines that are empty, so this if test ensures the line after only runs if it's not empty
    #Otherwise we might get AttributeError: 'NoneType' object has no attribute 'encode'
    if line.text is not None:
      #use regex to look for any or no character(s) followed by the string 'incident'
      #followed by any or no character(s) - the result is stored in 'mention'
      mention = re.match(r'.*bullying*', line.text)
      #if mention exists (there was a match, and it was created)
      if mention:
        #print the line numbers just before and after
        print range(linenumber-2,linenumber+1)
        #create 2 variables to store those lines for now - but have some default text
        linebefore = "EMPTY LINE"
        lineafter = "EMPTY LINE"
        incontextlist = []
        if pdfroot.xpath('.//text')[linenumber-2].text:
          linebefore = pdfroot.xpath('.//text')[linenumber-2].text
          incontextlist.append(linebefore)
          incontextlist.append(pdfroot.xpath('.//text')[linenumber-1].text)
        if pdfroot.xpath('.//text')[linenumber].text is not None:
          lineafter = pdfroot.xpath('.//text')[linenumber].text
          incontextlist.append(lineafter)
        record["mention in context"] = ''.join(incontextlist)
        record["linenumber"] = linenumber
        #we add .encode to avoid any unicode-related errors
        print line.text.encode('ascii', 'ignore')
        record['url'] = url
        record['text'] = line.text.encode('ascii', 'ignore')
        record['reportline'] = url+str(linenumber)
        print 'ALL DATA: ', record
        scraperwiki.sqlite.save(['reportline'],record)
  
  
  

scrapepdf(url)

#Some example URLs
schoolurleg = "https://reports.ofsted.gov.uk/inspection-reports/find-inspection-report/provider/ELS/140407"
pdfurleg = "https://reports.ofsted.gov.uk/provider/files/2631211/urn/103980.pdf"
searchurl = "https://reports.ofsted.gov.uk/inspection-reports/find-inspection-report/results/any/21/any/any/any/any/any/any/any/week/0/0#search4"

def scrapeschoolpage(schoolurl):
    print 'RUNNING'
    schoolhtml = requests.get(schoolurl).content
    root = lxml.html.fromstring(schoolhtml)
    pdflinks = root.cssselect('div.download-report-link a')
    for link in pdflinks:
        print link.text
        print link.attrib.get('href')
        #results are like: /inspection-reports/find-inspection-report/provider/ELS/103927
        pdfurl = 'https://reports.ofsted.gov.uk'+link.attrib.get('href')
        print 'FULL PDF LINK: ', pdfurl
        scrapepdf(pdfurl)
        

# Read in a page
html = requests.get(searchurl).content
#html2 = scraperwiki.scrape(html)
#convert to lxml object
root = lxml.html.fromstring(html)
schoollinks = root.cssselect('h2 a')
for link in schoollinks:
    print link.text
    print link.attrib.get('href')
    #results are like: /inspection-reports/find-inspection-report/provider/ELS/103927
    schoolurl = 'https://reports.ofsted.gov.uk'+link.attrib.get('href')
    print 'FULL SCHOOL LINK: ', schoolurl
    scrapeschoolpage(schoolurl)
