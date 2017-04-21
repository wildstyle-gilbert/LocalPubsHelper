from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import constants
import pdb
import urllib
import csv
import os
import sys
import shutil
import zipfile
import errno
import re


# debugging
# import pdb #use pdb.set_trace() to break


def createVI(myDOIs):

    global results

    # get current YYYYMMDD

    import datetime
    date = datetime.date.today()
    datecode = datetime.datetime.now().strftime("%Y%m%d")

    # format results
    results = []

    '''
    Loop through the DOIS to find information from each article page. add that info to lists.

    '''
    clean_journal = []

    # remove empty strings from list
    myDOIs = [doi for doi in myDOIs if doi]

    for DOI in myDOIs:

        DOI = DOI.strip()


        # collect journal prefixes
        cleanDOI = DOI.replace("10.1021/", "").replace(".", "")
        journalprefix = cleanDOI[:-7]
        clean_journal.append(cleanDOI)

        coden = constants.CODEN_MATCH[journalprefix]

        # create image URL for PB using coden and today's date.
        img_url = ("/pb-assets/images/selects/" + str(coden) +
                   "/" + str(datecode) + "/" + str(cleanDOI) + ".jpeg")

        # create article URL
        article_link = ("/doi/abs/" + str(DOI))

        # open selenium window
        # driver = webdriver.PhantomJS(service_log_path='/home/deploy/pubshelper/ghostdriver.log', executable_path="/home/deploy/pubshelper/phantomjs")
        # driver = webdriver.PhantomJS(executable_path="/usr/local/bin/phantomjs")
        # driver = webdriver.PhantomJS()

        print "\n\n -------- \n\n"

        print "instanciating webdriver"
        driver = webdriver.PhantomJS()
        print "setting window size"
        driver.set_window_size(1120, 550)

        # go to full article page by adding URL prefix to DOI
        print "getting doi link"
        driver.get("http://pubs.acs.org/doi/full/" + DOI)
        print "\t" + DOI

        # wait ten seconds and get title text to add to results object
        print "waiting then getting title text"
        try:
            title = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "hlFld-Title")))
            html_title = title.get_attribute('innerHTML').encode('utf-8')
            print "\t" + html_title
        except:
            print "\n" + DOI.upper() + " IS AN INVALID DOI \n"
            articleinfo = {
                'DOI': DOI,
                'Title': "Invalid DOI"
            }
            results.append(articleinfo)
            continue

        # add title to list of titles (with special characters)
        # article_titles.append(title.get_attribute('innerHTML').encode('utf-8'))

        # get authors
        print "getting authors"
        authors = driver.find_elements_by_xpath(constants.AUTHOR_XPATH)

        # join the text in the array of the correctly encoded authors
        authors_scrape = []
        for author in authors:
            authors_scrape.append(author.text.encode('utf-8'))


        # create array to hold formatted authors list (stars next to authors)
        authorsStars = []

        # iterate over authors_scrape and join * with author before it
        for index, i in enumerate(authors_scrape):
            if index != (len(authors_scrape)-1):
                if authors_scrape[index+1] == "*":
                    string = authors_scrape[index] + authors_scrape[index+1]
                    del(authors_scrape[index+1])
                    # add string
                    authorsStars.append(string)
                else:
                    authorsStars.append(authors_scrape[index])
            else:
                authorsStars.append(authors_scrape[index])

        # join correctly formatted authors
        # add ', ' and 'and'
        if len(authorsStars)==2:
            authorsStars.insert(1, ' and ')
            authorsjoined = (''.join(authorsStars))
        elif len(authorsStars)==1:
            authorsjoined = (''.join(authorsStars))
        else:
            all_but_last = ', '.join(authorsStars[:-1])
            last = authorsStars[-1]
            authorsjoined = ', and '.join([all_but_last, last])


        print "\t" + authorsjoined
        # Get citation info
        # CITATION_XPATH = "//*[@id=\"citation\"]"
        # journalcite = driver.find_elements_by_xpath(CITATION_XPATH)

        # citationprep = []
        # for part in journalcite:
        #     citationprep.append(part.text.encode('utf-8'))

        # fullcitation = (''.join(citationprep))

        # Get abbreviated Journal name
        print "getting journal name"
        JOURNAL_XPATH = "//*[@id=\"citation\"]/cite"
        journalscrape = driver.find_elements_by_xpath(JOURNAL_XPATH)

        for i in journalscrape:
            journal = i.text.encode('utf-8')

        print "\t" + journal
        # set up soup for BS4

        citationtag = driver.find_element_by_id("citation")
        outcitationtag = citationtag.get_attribute("outerHTML")
        soup = BeautifulSoup(outcitationtag, "html.parser")

        print "getting year"
        # set year to citation year or empty string
        try:
            year = soup.find("span", class_="citation_year").text
            if year is None:
                raise Exception
            else:
                year = year.encode("utf-8")

        except:
            year = ''
            print 'year not found'

        print "\t" + year
        # Get citation voume or set to empty string
        print "getting issue"
        try:
            volume = soup.find("span", class_="citation_volume").text
            if volume is None:
                raise Exception
            else:
                volume = volume.encode("utf-8")

        except:
            volume = ''
            print 'volume not found'
        print "\t" + volume
        # Get issue info or set to empty string
        print "getting issue info"
        try:
            issue_info = soup.find(
                "span", class_="citation_volume").next_sibling
            if issue_info is None:
                raise Exception
            issue_info = issue_info.encode("utf-8")

        except:
            issue_info = ''
            print 'issue not found'
        print "\t" + issue_info
        # click figures link and form url, or set to empty string
        print "getting figures link"
        try:
            driver.find_element_by_class_name('showFiguresLink').click()

            # get toc image href
            img_box = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "highRes")))
            if img_box is None:
                raise Exception
            toc_href = img_box.find_element_by_css_selector(
                'a').get_attribute('href')

        except:
            # toc_image = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "figBox")))
            # toc_href = toc_image.find_element_by_css_selector('img').get_attribute('src')
            toc_href = ""
            print 'no hi-res figure found'
        print "\t" + toc_href

        articleinfo = {
            'DOI': DOI,
            'Title': html_title,
            'article-link': article_link,
            'Authors': str(authorsjoined),
            'toc_href': str(toc_href),
            'Image': img_url,
            # "full-citation": fullcitation
            'Journal': journal,
            'Volume': volume,
            'Issue-info': issue_info,
            'Year': year,
            "Datecode": datecode,
            "Clean_doi": cleanDOI,
            'Coden': coden
            }


        driver.close()
        driver.quit()

        results.append(articleinfo)



    # write python dict to a csv file
    keys = results[0].keys()

    with open('app/vi-csv.csv', 'wb') as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)

    '''
    check to see if there is an existing folder for coden and date,
    if not, create the folder

    '''
    # create folder for journal coden and date stamp
    try:

        os.makedirs("app/static/img/generated/virtualissue/" + coden + '/' + \
            str(datecode) + "/")

    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise exc
        pass

    '''
    download images from list of image href

    '''

    for articleinfo in results:
        try:
            filename = "app/static/img/generated/virtualissue/" + coden + '/' + \
            str(datecode) + "/" + articleinfo["Clean_doi"] + '.jpeg'
        except:
            pass
        try:
            href = articleinfo["toc_href"]
        except:
            pass

        try:
            urllib.urlretrieve(href, filename)
        except IOError:
            print "No image found for " + DOI
            pass

    '''
    ZIP images using shutil

    '''
    filedirectory = "app/static/img/generated/virtualissue/" + \
        coden + '/' + str(datecode) + "/"

    shutil.make_archive(datecode, 'zip', filedirectory)
    shutil.copy(datecode + '.zip', filedirectory)

    return results
