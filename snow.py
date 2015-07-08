import nltk
import string
import re
import pybloomfilter
from optparse import OptionParser
import fileinput

def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]

#tags for colouring text
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

#regex for finding various ID related fields
postcode = re.compile('(GIR ?0AA|[A-PR-UWYZ]([0-9]{1,2}|([A-HK-Y][0-9]([0-9ABEHMNPRV-Y])?)|[0-9][A-HJKPS-UW]) ?[0-9][ABD-HJLNP-UW-Z]{2})',re.IGNORECASE)
natinsure = re.compile("\s*[a-zA-Z]{2}(?:\s*\d\s*){6}[a-zA-Z]?\s*")
phoneno= re.compile("\(?(?:(?:0(?:0|11)\)?[\s-]?\(?|\+)44\)?[\s-]?\(?(?:0\)?[\s-]?\(?)?|0)(?:\d{2}\)?[\s-]?\d{4}[\s-]?\d{4}|\d{3}\)?[\s-]?\d{3}[\s-]?\d{3,4}|\d{4}\)?[\s-]?(?:\d{5}|\d{3}[\s-]?\d{3})|\d{5}\)?[\s-]?\d{4,5}|8(?:00[\s-]?11[\s-]?11|45[\s-]?46[\s-]?4\d))(?:(?:[\s-]?(?:x|ext\.?\s?|\#)\d+)?)")
email = re.compile("[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}",re.IGNORECASE)
nhsno = re.compile("\d{3}\s?\d{3}\s?\d{4}")

def run():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    
    #commandline options
    parser.add_option("-f", "--file", dest="filename",help="read data from FILENAME")
    parser.add_option("-d", "--destroy", action="store_true", dest="d", help="aggressively anonymise")
    parser.add_option("-p", "--pos", action="store_true", dest="pos", help="use part of speech tagger")
    parser.add_option("-c", "--com", action="store_true", dest="common", help="remove words that are not in common")
    (options, args) = parser.parse_args()

    #read in the bloom filters
    names = pybloomfilter.BloomFilter.open("names.bloom")
    commonWords = pybloomfilter.BloomFilter.open("common.bloom")
    
    def checkMatch(position,word):
        lowerWord = word.lower()
        inNames =  lowerWord in names 
        if options.pos:
            #NNP is a proper noun in POS
            inNames &= (posData[position][1]== "NNP")
        if options.common:
            inNames &= not lowerWord in commonWords 
        return inNames

    ## if filename is given then use that
    ## otherwise use empty file list
    ## when fileinput.input is given an empty list stdin is used
    if options.filename:
        filelist = [options.filename]
    else:
        filelist = []
            
    #process on a line by line basis to avoid big buffers
    for line in fileinput.input(filelist,mode='rb'):
                ##check lines for postcode
                postcodes = re.findall(postcode, line)
                postcodes = [i[0] for i in postcodes]
                natinsures = re.findall(natinsure, line)
                phonenos = re.findall(phoneno, line)
                emails = re.findall(email, line)
                nhsnos = re.findall(nhsno, line)
                
                outString=""
                #we need to maintain tabs as they can be used as delimiters in tsv files
                tabPos = find(line,"\t")
                data = nltk.word_tokenize(line)
                posData = nltk.pos_tag(data)
                found = False
                if len(postcodes+natinsures+phonenos+emails+nhsnos)>0:
                    found=True
                #go through the line looking for _some_ matches
                for count,i in enumerate(data):
                    if checkMatch(count,i):
                        found = True
                        break
                    
                #if found write out in the appropriate way
                if found:
                    for count,i in enumerate(data):
                        if checkMatch(count,i):
                            #if destroy add _
                            if options.d:
                                outString += " _"
                            
                            #else if we are just showing the data
                            else:
                                #put colours around word
                                outString +=" " + bcolors.WARNING + i + bcolors.ENDC
                        else:
                            #rebuild the line from tokens
                            end = outString[-1] if len(outString)>0 else ""
                            #fix for punctuation
                            if i in string.punctuation or end =="@":
                                outString+=i 
                            else:
                                outString+=" "+ i
                        #sorted so big finds are treated first
                        for i in sorted(postcodes+natinsures+phonenos+emails+nhsnos,key=len,reverse=True):
                            if options.d:
                                outString = outString.replace(i,'_')
                            else:
                                outString = outString.replace(i,bcolors.WARNING + i + bcolors.ENDC)
                    for i in reversed(tabPos):
                        outString = outString[:i+1] + "\t" + outString[i+2:]
                    print outString.replace("``","\"").replace("''","\"")
                else:
                    #if in destroy mode 
                    if options.d:
                        print line,
    
if __name__ == "__main__":
    run()
