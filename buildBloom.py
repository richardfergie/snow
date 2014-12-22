import pybloomfilter
from nltk.corpus import words

def buildFilters():
    #read the first name data-source
    with open("first.txt","rb") as first:
        firstNames = first.readlines()
        firstNames = [i.strip().lower() for i in firstNames]
    #read the surname data source
    with open("surnames.txt","rb") as sur:
        surnames = sur.readlines()
        surnames = [i.strip().lower() for i in surnames]
    
    #build an all name bloom filter
    
    allnames = firstNames+surnames
    names = pybloomfilter.BloomFilter(1000000, 0.001, 'names.bloom')
    names.update(allnames)
    
    common = pybloomfilter.BloomFilter(1000000, 0.001, 'common.bloom')
    
    #build an NLTK dataset of common words - double check to remove firstname
    #and capitalized words
    outWords = filter(lambda x: x[0]==x[0].lower(),words.words())
    common.update(outWords)

if __name__ == "__main__":
    buildFilters()
    print "Build Complete"