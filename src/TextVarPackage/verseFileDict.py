'''
Created on Apr 14, 2015
ToDo:
create filter for files without: //tei:altIdentifier[@type="edition"]/tei:idno/text()'
or fallback to other Identifiers
What is oS???? -> faustwiki
writing the dict the other way round might be better performance vise

@author: MHuber
'''

from lxml import etree
import glob
import json
import re
import requests
from requests.auth import HTTPBasicAuth



fileList1 = []
fileVerseDict = {}
parser = etree.XMLParser(recover=True, encoding = 'utf-8')
documentSigle=[]

def readLocalXML(filePath):
    for item in glob.glob(filePath):
        fileList1.append(item)
        print(fileList1)
    print('------readLocalXML succesful--------')

##
#not used yet
#requires the directory where the json should be stored
#reads the xmlfiles to create a dict (as json file) of the Sigle - verse correlation
def xmlParseAndDump(filePathToJson):        
    parser = etree.XMLParser(recover=True, encoding = 'utf-8')
    for item in fileList1:
        with open (item,'r', encoding='utf-8') as f:
            lineNumberList = []
            doc = etree.parse(f, parser)
            documentSigle = doc.xpath('//tei:altIdentifier[@type="edition"]/tei:idno/text()' , namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
            print(item)
            print(documentSigle)
            #documentSigle is a list of strings!
            lList = doc.xpath("//tei:l[@n]", namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
            for line in lList:
                lineNumber = line.get("n")
                if re.match("^\d+$", lineNumber):
                    lineNumberList.append(lineNumber)
            if (documentSigle):
                
                sigle = documentSigle[0]
                if (sigle=="oS"):
                    printSigle = doc.xpath('//tei:altIdentifier[@type="print"]/tei:idno/text()', namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
                    sigle = printSigle[0]
                fileVerseDict[sigle] = lineNumberList
            else:
                #works only if glob.glob gives back strings
                idno = doc.xpath('//tei:msIdentifier/tei:idno/text()', namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
                print(item)
                if (idno):
                    fileVerseDict[idno[0]] = lineNumberList
    print(fileVerseDict)
    print(json.dumps(fileVerseDict, sort_keys=True, indent=4))
    ##
    #buggy!
    with open (filePathToJson, mode = 'w', encoding='utf-8') as f:
        json.dump(fileVerseDict, f)
        print('json dumped')


##
#loads jsonFile and transforms it in a jsonFile like lineNumber:File-id1, File-id2...
def jsonReadAndTransform(inputFile, outputFile):
    verseFileDict1 = {}
    with open (inputFile,'r', encoding='utf-8') as f:
        fileVerseDict1 = json.load(f, encoding='utf-8')
        #print (fileVerseDict1)
        print (type (fileVerseDict1))
        print('-------------------')
    for key, item in fileVerseDict1.items():
        print(key, ': ', item)
    
            

    for identifier, lineNumberList in fileVerseDict1.items():
        if (lineNumberList):
            for lineNumber in lineNumberList:
                verseFileDict1.setdefault(lineNumber,[]).append(identifier)
    print(verseFileDict1)
    with open(outputFile, mode ='w', encoding='utf-8') as f:
        json.dump(verseFileDict1, f)
    

def createVerseFilePath(outputfilePath):
    parser = etree.XMLParser(recover=True, encoding = 'utf-8')#unnoetig?
    verseFilePath = {}
    for item in fileList1:
        with open (item,'r', encoding='utf-8') as f:
            doc = etree.parse(f, parser)
            print(item)
            lList = doc.xpath("//tei:l/@n", namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
            for lineNumber in lList:
                if re.match("^\d+$", lineNumber):
                    verseFilePath.setdefault(lineNumber, []).append(item)
    with open(outputfilePath, mode='w', encoding='utf-8') as f:
        json.dump(verseFilePath, f)

def readOnlineXML(filePathToSample):

    url = "https://faustedition.uni-wuerzburg.de/xml/transcript/gsa"
    r = requests.get(url, auth=HTTPBasicAuth('MHuber', 'mushroom87') )
    temp =r.text


    refList=re.findall(r'(?<=\>)\d{6}', temp)
    for urlExtension in refList:

        newURL = url+"/"+urlExtension +"/" + urlExtension + ".xml"
        print(newURL)
        s =requests.get(newURL, auth=HTTPBasicAuth('MHuber', 'mushroom87'))
        with open(filePathToSample + urlExtension,'w', encoding="utf-8") as f:
            f.write(s.text)
    print('readOnlineXML done')

readOnlineXML('/Users/MHuber/Documents/python/testFolder/')
readLocalXML('/Users/MHuber/Documents/python/testFolder/*') 
#xmlParseAndDump('/Users/MHuber/Documents/python/fileVerse.json')
#jsonReadAndTransform('/Users/MHuber/Documents/python/fileVerse.json', '/Users/MHuber/Documents/python/verseFile.json')       
createVerseFilePath('/Users/MHuber/Documents/python/verseFilePath.json')        
