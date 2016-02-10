"""
Create a .bt Binary Template for 010 Editor from a TrID's definition
"""

PROGRAM_VER = "0.61b"

import sys
import xml.etree.ElementTree as ET
import random
import argparse
import string

def header_intro():
    """
    Show some credits.
    """
    print
    print "TrID2bt v%s - (C) 2016 Marco Pontello" % (PROGRAM_VER)
    print


def hex2bytes(string):
    """
    Convert a list of HEX values to a bytes sequence
    """
    bytes = []
    for i in range(0, len(string), 2):
        bytes.append(chr(int(string[i:i+2], 16)))
    return "".join(bytes)


class TrIDDefLite():
    """
    Define the bare minimum needed for a TrID definition.
    """
    def __init__(self):
        self.filetype= ""
        self.ext= ""
        self.patterns= []
        self.strings= []
    def __str__(self):
        text = "FileType: '%s', Ext: '%s', Patterns: %d, Strings: %d" % \
               (self.filetype, self.ext,
               len(self.patterns), len(self.strings))
        return text


def load_trid_def(filename):
    """
    Parse a TrID's XML definition and return a TrIDDefLite object
    """
    triddef = TrIDDefLite()

    try:
        trid = ET.parse(filename).getroot()

        triddef.filetype = trid.find("Info/FileType").text
        #consider only the first extension
        triddef.ext = trid.find("Info/Ext")
        if triddef.ext.text:
            triddef.ext = triddef.ext.text.split("/")[0]
        else:
            triddef.ext = ""

        elist = trid.findall("FrontBlock/Pattern")
        for pat in elist:
            for patdata in pat.getchildren():
                ppos = 0
                bytes = ""
                if patdata.tag == "Pos":
                    ppos = int(patdata.text)
                elif patdata.tag == "Bytes":
                    pbytes = hex2bytes(patdata.text)
            triddef.patterns.append( (ppos, pbytes) )

        elist = trid.findall("GlobalStrings/String")
        for ele in elist:
            #decodes the zeros-bytes
            triddef.strings.append(ele.text.replace("'", "\x00").upper())

    except IOError:
        print "* Error: unable to access TrID's definition."
    except ET.ParseError as detail:
        print "* Error: XML -", detail
    except:
        print "* Error:", sys.exc_info()[0]

    return triddef

def bytes2c(buff):
    """
    Convert a byte buffer to a 'c style' literal constant
    """
    text = []
    printables = string.digits + string.letters
    for c in buff:
        if c in printables:
            text.append(c)
        else:
            text.append("\\x"+hex(ord(c))[2:])
    return "".join(text)

def writebt(triddef, btname):
    """
    Create a binary template using the patterns from the given
    TrID definition.
    """

    text = ("// TrID2bt v%s - 010 Editor Binary Template generator\n\n" %
            (PROGRAM_VER) )

    text += 'Printf( "TrID filetype: %s\\n");\n' % (triddef.filetype)
    text += "local int errs = 0;\n\n"

    #evaluate patterns
    patnum = 0
    for pat in triddef.patterns:
        pos = pat[0]
        patbytes = pat[1]
        patnum += 1
        
        text += "FSeek(%d);\n" % (pos)
        text += "char patt%d[%d] <bgcolor=cAqua>;\n" % (patnum, len(patbytes))
        text += 'if (patt%d != "%s") {\n' % (patnum, bytes2c(patbytes))
        text += '  errs++;\n'
        text += '  Printf( "patt%d doesn''t match!\\n");\n' % (patnum)
        text += '  if (errs==1) SetCursorPos(%d);\n' % (pos)
        text += '}\n'
        
        text += "\n"


    text += 'Printf( "Marked %%d pattern(s)\\n", %d );\n' % (len(triddef.patterns))
    text += 'if (errs > 0) Printf( "*** Wrong matches: %d ***", errs );\n'


    print "Writing file '%s'" % (btname)

    try:
        f = open(btname, "w")
        f.write(text)
        f.close()
    except:
        print "* Error: unable to write file!"


def get_cmdline():
    """
    Evaluate command line parameters, usage & help.
    """
    parser = argparse.ArgumentParser(
             description="Create fake files from a TrID's definition",
             prefix_chars='-',
             version = "TrID2Files/Python v" + PROGRAM_VER)
    parser.add_argument("filename", action="store",
                        help = "TrID's defintion")
    parser.add_argument("tempname", action="store", default="new.bt",
                        nargs="?", help="binary template to create")
    res = parser.parse_args()

    param = {}
    param["filename"] = res.filename
    param["btname"] = res.tempname
    return param


def main():
    header_intro()
    params = get_cmdline()

    filename = params["filename"]
    btname = params["btname"]

    print "Reading TrID's definition '%s'..." % (filename)
    triddef = load_trid_def(filename)
    if len(triddef.patterns) == 0:
        print "Not enough info available."
        sys.exit(1)

    print "FileType :", triddef.filetype
    print "Extension:", triddef.ext
    print "Patterns :", len(triddef.patterns)
    print "Strings  :", len(triddef.strings)

    writebt(triddef, btname)

    print "Done."


if __name__ == "__main__":
    main()

