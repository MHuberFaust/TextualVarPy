import glob
#import os
import re
import json
from lxml import etree
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
settings.configure()

from django import template

#ToDo:

#correct style attributes or write a css-file
#get rid of global variables
#change parseEtree to only access the selected lines
#refine xpath-expression and verse selection
#refine function structure
#put Sigle in html output (//altIdentifier[@type="edition"]/idno/text())
#filter out redundant/the same verses. Probably RE after xpath query -> needs testing with bigger corpus




###################################################################
#Variables
###################################################################
fileList=[]
fileList1=[]
objectToParse = {}
pythonTempList=[]
contextObjectList = []
#t = 'insert filePath to template'

##
#"dialog"-function
#let the user choose between two use-cases typical for scholarly editions:
##1. shows all text lines of a document // not sure if it is worth implementing
##2. shows textual variance of a text line

def inputConsole(inputVerseFilePath):
    
    
    consoleInput = input('Please write one or several verse numbers separated by a comma to see their variance in Goethes Faust')
    
    #do stuff with consoleInput
    inputLineList = []
    fileList=[] #delete either the global variable fileList or the local one
    with open (inputVerseFilePath,'r', encoding='utf-8') as f:
        
        verseFilePathDict = json.load(f, encoding='utf-8')
        if (re.fullmatch('\d{1,6}', consoleInput)):
            if not (verseFilePathDict.get(consoleInput)):
                print('Can not find line ' + consoleInput)
            else:
                fileList = verseFilePathDict[consoleInput]
                inputLineList.append(consoleInput)
        else:
            inputTempList = re.split('\d{1,6}', consoleInput)
            for inputTemp in inputTempList:
                if (re.fullmatch('\d{1,6}', inputTemp)):
                    if not (verseFilePathDict.get(consoleInput)):
                        print('Can not find line ' + consoleInput)
                else:        
                    fileList.append(verseFilePathDict[inputTemp])
                    inputLineList.append(inputTemp)
    parseXML(fileList,inputLineList)

        
    

##
#reads all files of the given directory and calls parseXML() with fileList
def readLocalXML(filePath):
    for item in glob.glob(filePath):
        fileList.append(item)
        print(item)
    parseallXML(fileList)
    print('readLocal() done')
    






##
#fetches data from https://faustedition.uni-wuerzburg.de/xml/
#and saves it at filePathToSample
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

##
# Be careful: deletes whitespace!
# parses an XML and calls parseEtree()
def parseallXML(fileList):
    
        #recover=True for potentially broken XML (several crashes indicated that there is broken XML in the collection)
    parser = etree.XMLParser(recover=True, encoding = 'utf-8')
    for item in fileList:
        lList=[]
        with open (item,'r', encoding='utf-8') as f:
            doc = etree.parse(f, parser)
            lList = doc.xpath("//tei:l[@n]", namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
        #print (len(lList))
        for line in lList:
            lineNumber = line.get("n")

        #there are attributes "n = 1234-5678" with a range of verses,
        #indicating that the original verse/line is related to several verses in a later state.
        #a combination of split() and a more complex RE is needed to handle this
        #change verseFileDict according to it
            if re.match("^\d+$", lineNumber):

            #ignores inline-Elements! more complex XPath-Expression required
                lineText = etree.tostring(line, encoding="unicode", method="text")
                #print (lineNumber)
                #print (lineText)
            #if lineAlready exists-> ignore
            #not tested yet! should work though
                if (objectToParse.get(lineNumber)):
                    for equalLine in objectToParse[lineNumber]:
                        if not (lineText==equalLine):
                            objectToParse[lineNumber].append(lineText)
                    else:
                        objectToParse.setdefault(str(lineNumber),[]).append(lineText)
    
        print ('parseEtree() done')
    print (objectToParse)
    #else:
        #for item in fileList:
            #doc = etree.fromstring(item)
            #parseEtree(doc)
    print('parseXML done')

def parseXML(fileList,inputLineList):
    print('fileList')
    print(fileList)
    print('------------------')
    print('inputLineList')
    print(inputLineList)
    print('------------------')
    
    #recover=True for potentially broken XML (several crashes indicated that there is broken XML in the collection)
    parser = etree.XMLParser(recover=True, encoding = 'utf-8')
    xpathVarList=[]

    for inputLineNumber in inputLineList:
        xpathVarList.append("//tei:l[@n="+inputLineNumber+"]")
    xpathVar = '|'.join(xpathVarList)
    print('------xpathVar-----')
    print(xpathVar)
    print('--------------------')  
    for item in fileList:
        lList=[]
        sigle = ""
           
        with open (item,'r', encoding='utf-8') as f:
            doc = etree.parse(f, parser)
            #write variable for xpath with //tei:l[@n="inputLineListitem1|inputLineListItem2..."]
            
            ########new stuff 1406
            sigle = doc.xpath("//tei:altidentifier[@type='edition']tei:idno/text()", namespaces = {"tei":"http://www.tei-c.org/ns/1.0"})
            if not (sigle):
                sigle = doc.xpath("//tei:altidentifier[@type='print']tei:idno/text()", namespaces = {"tei":"http://www.tei-c.org/ns/1.0"})
            if not (sigle):
                sigle = doc.xpath("//tei:altidentifier[@type='repository']tei:idno/text()", namespaces = {"tei":"http://www.tei-c.org/ns/1.0"})
            if not (sigle):
                sigle = doc.xpath("//tei:msIdentifier/tei:idno/text()",  namespaces = {"tei":"http://www.tei-c.org/ns/1.0"})
            ######################    
            lList = doc.xpath(xpathVar, namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
        #print (len(lList))
        for line in lList:
            lineNumber = line.get("n")
            

        #there are attributes "n = 1234-5678" with a range of verses,
        #indicating that the original verse/line is related to several verses in a later state.
        #a combination of split() and a more complex RE is needed to handle this
        #change verseFileDict according to it
            if re.match("^\d+$", lineNumber):


            #ignores inline-Elements! more complex XPath-Expression required
                lineText = etree.tostring(line, encoding="unicode", method="text")
                print (lineNumber)
                print (lineText)
            #if lineAlready exists-> ignore
            #not tested yet! should work though
            #did not work; maybe because of the whitespace?
            #doubled the lineText
            #    if (objectToParse.get(lineNumber)):
            #        for equalLine in objectToParse[lineNumber]:
            #            if not (lineText==equalLine):
            #                objectToParse[lineNumber].append(lineText)
            #    else:
                objectToParse.setdefault(lineNumber,[]).append(lineText)#removed str cast
##add Sigle to objectToParse here!
                #objectToParse.setdefault(lineNumber,[]).append(sigleLine.setdefault(sigle, lineText)
                #the special case that one line appears several times on the same manuscript is not covered this way
        print ('parseEtree() done')
    print('----objectToParse-----')
    print (objectToParse)
    print('----------------------')
    #else:
        #for item in fileList:
            #doc = etree.fromstring(item)
            #parseEtree(doc)
    print('parseXML done')

    




def sortUpload():
    #error prone if there are more then 26 variations
    charArray =["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]


    url = 'http://collatex.net/demo/collate'
    headers = {'content-type':'application/json',
                'accept':'application/json'}
    #CollateX only accepts json objects in a specific format: for more information: CollateX documentation
    for key, value in sorted(objectToParse.items()):
        difLines = {}
        for index, singleLine in enumerate(value):
            awitness = {"id":charArray[index],"content":singleLine}
            difLines.setdefault("witnesses",[]).append(awitness)
        ##old code:    
        #i = 0
        #while i < len(value):
            #awitness ={"id": charArray[i], "content":value[i]}
            #difLines.setdefault("witnesses",[]).append(awitness)
            #i = i + 1

    


        #change http header as CollateX provides several possible outputs
        #"if(r.status_code==requests.codes.ok):" produces an error...
        # with pydev extension for eclipse, but it is an known error
        #check CollateX documentation concerning the formatting
        print('wololodiflinescoming')
        print(difLines)
        r= requests.post(url, data=json.dumps(difLines),headers=headers)
        if(r.status_code==requests.codes.ok):
            data =json.loads(r.text)
            print((data))
            pythonTempList.append(data)
##add Siglen to pythonTempList for further processing
        else:
            print(r.status_code)
            print(('something is wrong with ' + str(key)))
            continue

        print('wololodiflinescoming')
        print(difLines)
        
#Creates Context for the django template
def createContext():
    
    print(('start'))
    #t = Template('insertDirectorythingy')
    for coldata in pythonTempList:
        contextObject ={}
        print (('--------coldata--------'))
        print ((coldata))
        #print ((coldata['table']))
        for variance in coldata['table']:
            print('-------variance--------')
            print ((variance))

            for index, tokenset in enumerate(variance):
                print('-------tokenset-----')
                print ((tokenset))

                contextObject.setdefault(index,[]).append(tokenset)
                #a contextObject should look like {1:['a','b','v','v']['aasd','asd','afds']}
        contextObjectList.append(contextObject)
                    #samplecolddata: {'witnesses': ['A', 'B'], 'table': [[['Ein '], ['Ein ']], [['ewges '], ['ewiges ']], [['Meer\n               '], ['Meer']], [[], [',\n                ']]]}
    print('-----------------------contexObjectList-------------------------')
    print((contextObjectList))
    print('createContext() done')
    #return contextObjectList

def renderContext():
    htmlString ="""
<html>
    <head>
        <title>
        Textual Variance
        </title>
    </head>
    <body>
        <h1>Apparatus</h1>
        <div>Dict-Key (change List to dict)</div>
        {% for contextObject in contextObjectList %}
        <table style ="border-width:1px; border-style:solid">
            <thead>
                <tr>
                    <th>Sigle</th>
                    <th>verse//line content</th>
                </tr>
            </thead>
            <tbody>
                {% for key, value in contextObject.items %}
                    <tr>
                        <td>verse Sigle placeholder {{ key }}</td>
                        <td>
                            {% for varianceList in value %}
                                
                                <div style = "border-width:1px; border-style:solid">
                                    {% for item in varianceList %}
                                        {{ item }}
                                    {% endfor %}
                                </div>
                                
                            {% endfor %}
                        </td>
                {% endfor %}
            </tbody>
         </table>   
        {% endfor %}
    </body>
</html>"""
    t = template.Template(htmlString)
    c = template.Context({'contextObjectList' : contextObjectList})
    renderedTemp = t.render(c)
    print (renderedTemp)
    with open('/Users/MHuber/Documents/python/newHtml.html','w', encoding ='utf-8') as f:
        f.write(renderedTemp)
    #print((t.render(c)))






###################################################
#function call
###################################################

inputConsole('/Users/MHuber/Documents/python/verseFilePath.json')
#readLocalXML('/Users/MHuber/Documents/python/testFolder/*')
#readOnlineXML('/Users/MHuber/Documents/python/testFolder/')
#parseXML()
sortUpload()
createContext()
renderContext()