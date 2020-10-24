#!/usr/bin/env python
# coding: utf-8

# #### Create a list of lines from PDF using PDFMiner

# In[1]:


example_file = "C:/Users/ASUS/Desktop/A1861-5.pdf"
folder = ""


# In[2]:


import re
import regex
import copy
import Levenshtein
from fuzzywuzzy import fuzz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTChar, LTTextLineHorizontal, LTRect, LTLine


document = []

for page_layout in extract_pages(example_file):
    line_margin_list = []
    for element in page_layout:
        if isinstance(element, LTTextBoxHorizontal):
            for text_line in element:
                flag = False
                if regex.search(r"^[\p{Pd}_]*$", text_line.get_text().strip()) is not None:
                    continue
                else:
                    for character in text_line:
                        if isinstance(character, LTChar):
                            if 'bold' in character.fontname.lower() and character._text.isalnum():
                                flag = True
                                break;
                    temp = []
                    temp.append(round(text_line.x0,0))
                    temp.append(text_line.y0)
                    temp.append(text_line.y1)
                    #pre-process the text
                    clean_text = re.sub(' +', ' ', text_line.get_text().strip()).strip()
                    temp.append(clean_text)
                    if flag:
                        temp.append('BOLD')
                    else:
                        temp.append('NOT BOLD')
                    temp.append([text_line])
                    temp.append(page_layout.pageid)
                    line_margin_list.append(copy.deepcopy(temp))
                    
        if isinstance(element, LTRect) and (round(element.width,4) in (140.16,144,144.02,144.05)) and int(element.height)==0:
            temp = []
            temp.append(round(element.x0,0))
            temp.append(element.y0)
            temp.append(element.y1)
            temp.append("------------LTRect Footnote------------")
            temp.append('NOT BOLD')
            temp.append([element])
            temp.append(page_layout.pageid)
            line_margin_list.append(copy.deepcopy(temp))
        
        if isinstance(element, LTLine) and element.y0<150 and element.width>0 and element.width<200 and element.x0>0 and element.x0<100:
            temp = []
            temp.append(round(element.x0,0))
            temp.append(element.y0)
            temp.append(element.y1)
            temp.append("------------LTLine Footnote------------")
            temp.append('NOT BOLD')
            temp.append([element])
            temp.append(page_layout.pageid)
            line_margin_list.append(copy.deepcopy(temp))
            
    x = []
    x = sorted(line_margin_list, key = lambda x: x[0])        
    x = sorted(x, key = lambda x: x[1], reverse = True)
    hasPageNo = False
    if x[-1][3] == str(page_layout.pageid):
        del x[-1]
        hasPageNo = True
    else:
        if hasPageNo:
            if isinstance(x[-1][3], int):
                del x[-1]
        else:
            pass
        #print("There is no line containing Page Number to delete.")
    document.extend(copy.deepcopy(x))


# #### Remove Footnotes

# In[3]:


docWithoutFootnotes = []
temp_flag = False
for line in document:
    if line[3] == '------------LTRect Footnote------------' or line[3] == '------------LTLine Footnote------------':
        temp_flag = True
    if temp_flag:
        if last_line_y0 < line[1]:
            temp_flag = False
    if not temp_flag:
        docWithoutFootnotes.append(copy.deepcopy(line))
    last_line_y0 = line[1]


# #### Fixing parts of lines that are on same level but still are divided

# In[4]:


Lines = []
for i, line in enumerate(docWithoutFootnotes):
    if i == 0 or line[1] != docWithoutFootnotes[i-1][1]:
        Lines.append(copy.deepcopy(line))
    elif line[1] == docWithoutFootnotes[i-1][1]:
        Lines[-1][3] += ' ' + line[3]
        if Lines[-1][4] == 'BOLD' or line[4] == 'BOLD':
            Lines[-1][4] == 'BOLD'
        else:
            Lines[-1][4] == 'NOT BOLD'
        Lines[-1][5].extend(copy.deepcopy(line[5]))


# #### Fixing line gap due to references and minimizing the top coordinate of line

# In[5]:


for line in Lines:
    minimum_top = line[2]
    for text_line in line[5]:
        for character in text_line:
            if isinstance(character, LTChar):
                if minimum_top > character.y1 and character._text!= ' ':
                    minimum_top = character.y1
    line[2] = minimum_top


# In[6]:


# CLASS FOR INDENTATION IN PARAGRAPHS

counter = [-1]
class Node:
    def __init__(self, indented_line, lev):
        self.children = []
        self.level = lev
        self.text = indented_line.strip()

    def add_children(self, nodes):
        childlevel = nodes[0].level
        while nodes:
            node = nodes.pop(0)
            if node.level == childlevel: # add node as a child
                self.children.append(node)
            elif node.level > childlevel: # add nodes as grandchildren of the last child
                nodes.insert(0,node)
                self.children[-1].add_children(nodes)
            elif node.level <= self.level: # this node is a sibling, no more children
                nodes.insert(0,node)
                return

    def as_dict(self):
        global counter
        counter[-1] += 1
        dictionary = {}
        
        if len(self.children) > 1:
            _id = counter[-1]
            counter.append(-1)
            temp = {}
            for node in self.children:                
                temp.update(node.as_dict())
            
            dictionary[_id] = {'text': self.text, 'contains': temp}
            counter.pop()
            return dictionary
        
        elif len(self.children) == 1:
            _id = counter[-1]
            counter.append(-1)
            dictionary[_id] = {'text': self.text, 'contains': self.children[0].as_dict()}
            counter.pop()
            return dictionary
        
        else:
            _id = counter[-1]
            counter.append(-1)
            dictionary[_id] = self.text
            counter.pop()
            return dictionary


# In[7]:


def clear_references(line):
    pattern = re.compile(r'[0-9]+\s?\[.*?\]')
    st = list(line)    
    if re.search(pattern, line) is not None:
        finditer = re.finditer(pattern, line)
        for thing in finditer:
            st[thing.end()-1] = ''
        new_line = "".join(st)
        new_line = re.sub(r'[0-9]+\s?\[','',new_line).strip()
        return new_line
    elif re.search(r'[0-9]+\s?\[.*', line) is not None:
        new_line = re.sub(r'[0-9]+\s?\[','',line).strip()
        return new_line
    elif re.search(r'\*', line) is not None:
        new_line = re.sub(r'\*','',line).strip()
        return new_line
    else:
        return line


# In[8]:


def remove_superscript(line):
    string = ''
    for text_line in line[5]:
        for character in text_line:
            if isinstance(character, LTChar) and character._text.isdigit() and character.size < 8.5:
                continue
            string += str(character._text)
    clean_text = re.sub(' +', ' ', string.strip()).strip()
    
    new_line = regex.sub(r'[\[\]\*]', '', clean_text).strip()
    return new_line


# In[9]:


def remove_punct(line):
    return regex.sub(r'[\p{Pd}\.]', '', line).strip()


# In[10]:


pdf_dict = {}

def act_id(Lines):
    start_index = None
    for i, line in enumerate(Lines):
        if re.search("^SECTION[S]?\.?$", line[3]) is not None:
            start_index = i
            break
    
    for i, line in enumerate(Lines[start_index:]):
        if regex.search("^ACT\p{P}*\s?NO\p{P}*\s?[0-9]+\s?OF\s?[0-9]+$", clear_references(line[3]), flags=regex.I) is not None or regex.search("^NO\p{P}*\s?[0-9]+\s?OF\s?[0-9]+$", clear_references(line[3]), flags=regex.I) is not None:
            return line[3]
    raise Exception("ACT ID NOT FOUND!")

def enactment_date(Lines, actID):
    start_index = None
    x = None
    
    for i, line in enumerate(Lines):
        if line[3] == actID:
            start_index = i
            break
    
    for i, line in enumerate(Lines[start_index:]):
        if re.search("^\[.*\]\s*\.?$", line[3]) is not None:
            x = line[3]
            break
    return x

def act_title(Lines):
    string = ''
    for line in Lines:
        if regex.search(r"^((ARRANGEMENT\s?OF\s?SECTION[S]?){e<4}|C\s*O\s*N\s*T\s*E\s*N\s*T\s*S)$", line[3], flags=regex.I) is not None:
            string = string.strip()
            break
        string += line[3] + ' '
    return string


# In[11]:
# EXtract ACT ID, ACT TITLE, ENACTMENT DATE

actID = act_id(Lines)
actDate = enactment_date(Lines, actID)

pdf_dict['Act Title'] = act_title(Lines)
pdf_dict['Act ID'] = actID
pdf_dict['Enactment Date'] = actDate
pdf_dict


# In[12]:


def act_definition(Lines, actDate):
    flag = False
    definitionFound = False
    arg_list = []
    string_indent = [-1,'']
    indent = []
    flag = False
    start_1 = None
    
    for i, line in enumerate(Lines):
        if line[3] == actDate.strip():
            start_1 = i
            break

    Lines = Lines[start_1:]
    
    for i, line in enumerate(Lines):
        if re.search("^(an\s+act|preamble).*", clear_references(line[3]), flags=re.I) is not None and not flag:
            indent.append(line[0])
            last_line_x0 = line[0]
            last_line_y0 = line[1]
            string_indent[0] = line[0]
            string_indent[1] += line[3]
            flag = True
            definitionFound = True
            continue
            
        if re.search("(be it enacted|it is enacted|it is hereby enacted)", clear_references(string_indent[1]), flags=re.I) is not None:
            start_2 = re.search("(be it enacted|it is enacted|it is hereby enacted)", clear_references(string_indent[1]), flags=re.I).start()
            if start_2 != 0:
                start_2 = re.search("(be it enacted|it is enacted|it is hereby enacted)", string_indent[1], flags=re.I).start()
                string_indent[1] = string_indent[1][:start_2]
            else:
                string_indent[1] = ''
            if len(string_indent[1].strip()) != 0:
                level = indent.index(string_indent[0])
                arg_list.append(Node(string_indent[1].strip(), level))
            string_indent[0] = -1
            string_indent[1] = ''
            flag = False
            break
            
        if flag:
            add_newline = ' '
            if clear_references(line[3].upper()).startswith('WHEREAS') or clear_references(line[3].upper()).startswith('PREAMBLE'):
                if len(string_indent[1].strip()) != 0:
                    level = indent.index(string_indent[0])
                    arg_list.append(Node(string_indent[1].strip(), level))
                indent.clear()
                string_indent[0] = line[0]
                string_indent[1] = ''
                if line[0] not in indent:
                    indent.append(line[0])
            
            if Lines[i-1][6] != line[6]:              # if we jump to new page in content
                if (line[0] > last_line_x0):
                    if len(string_indent[1].strip()) != 0:
                        level = indent.index(string_indent[0])
                        arg_list.append(Node(string_indent[1].strip(), level))
                    string_indent[0] = line[0]
                    string_indent[1] = ''
                    if line[0] not in indent:
                        indent.append(line[0])

                if (line[0] <= last_line_x0) and (line[0] in indent) and (re.search("^[a-z].*", line[3]) is None):
                    if len(string_indent[1].strip()) != 0:
                        level = indent.index(string_indent[0])
                        arg_list.append(Node(string_indent[1].strip(), level))
                    if line[0] < last_line_x0:
                        while bool(indent) and indent[-1] > line[0]:
                            indent.pop()
                        if line[0] not in indent:
                            indent.append(line[0])
                    string_indent[0] = line[0]
                    string_indent[1] = ''

            else:
                if (line[0] > string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                    if len(string_indent[1].strip()) != 0:
                        level = indent.index(string_indent[0])
                        arg_list.append(Node(string_indent[1].strip(), level))
                    string_indent[0] = line[0]
                    string_indent[1] = ''
                    if line[0] not in indent:
                        indent.append(line[0])

                if (line[0] <= string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):     # CHANGED
                    if len(string_indent[1].strip()) != 0:
                        level = indent.index(string_indent[0])
                        arg_list.append(Node(string_indent[1].strip(), level))
                    if line[0] < string_indent[0]:
                        while bool(indent) and indent[-1] > line[0]:
                            indent.pop()
                        if line[0] not in indent:
                            indent.append(line[0])
                    string_indent[0] = line[0]
                    string_indent[1] = ''

            last_line_x0 = line[0]
            last_line_y0 = line[1]
            string_indent[1] += add_newline + line[3]
            
          

    if definitionFound == False:
        return None
    else:
        global counter
        counter = [-1]
        root = Node('root', 0)
        root.add_children(arg_list)
        d = root.as_dict()[0]['contains']
        return d


# In[13]:
# Extract ACT DEFINITION

actDefinition = act_definition(Lines, actDate)


# In[14]:


if actDefinition is not None:
    pdf_dict["Act Definition"] = actDefinition
actDefinition


# In[15]:


def sections_list(Lines, actDate):
    list_of_sections = []
    omittedSectionList = []
    schedule_index = -1
    
    flag = False
    pageno = None
    
    for line in Lines:
        if line[3] == actDate:
            pageno = line[6]
            break

    for i, line in enumerate(Lines):
        if re.search("^SECTION[S]?\.?$", line[3]) is not None:
            flag = True
            continue
        
        if flag and line[6] == pageno:
            flag = False
            break
        
        if flag:
            if re.search("^[0-9]+\-?[A-Z]*\s*\.\s*.*", line[3]) is not None:
                mo = re.search(r"(^([0-9]+\-?[A-Z]*)\s*\.\s*(.*))", line[3])
                sec_id = mo.group(2).strip()
                sec_name = mo.group(3).strip()
                
                if re.search("^\[?\s*(Omitted|Repealed)\s*\.?\s*\]\s*\.?$", sec_name, flags=re.I) is not None:      # for omitted and repealed
                    if sec_name.lower().find('omitted')!=-1 or sec_name.lower().find('repealed')!=-1:
                        omittedSectionList.append([sec_id,sec_name])
                    schedule_index = i
                    list_of_sections.append([sec_id,sec_name])
                else:
                    inc = 1
                    while True:
                        if sec_name[-1]!='.':
                            if re.search("^[0-9]+\-?[A-Z]*\s*\.\s*.*", Lines[i+inc][3]) is None and regex.search(r"\b(SCHEDULE|APPENDIX|ANNEXURE){e<3}\b", Lines[i+inc][3], flags=regex.I) is None:
                                if re.search("^SECTION[S]?\.?$", Lines[i+inc][3]) is not None:
                                    inc += 1
                                    continue                                
                                sec_name = sec_name + ' ' + Lines[i+inc][3].strip()
                                inc += 1
                            else:
                                sec_name = sec_name + '.'
                                break
                        else:
                            break
                    schedule_index = i + (inc-1)
                    list_of_sections.append([sec_id,sec_name])
                    
            elif regex.search(r"\b(SCHEDULE|APPENDIX|ANNEXURE){e<3}\b", line[3], flags=regex.I) is not None or re.search('^FORM\s*\.?$', line[3]) is not None:
                break
                
    return list_of_sections, omittedSectionList, schedule_index+1


# In[16]:


def schedule_list(Lines, actDate):
    list_of_schedules = []
    omittedScheduleList = []
    pageno = None
    
    for line in Lines:
        if line[3] == actDate:
            pageno = line[6]
            break

    for i, line in enumerate(Lines):        
        if line[6] == pageno:
            break
        if regex.search(r"\b(SCHEDULE|APPENDIX|ANNEXURE){e<3}\b", line[3], flags=regex.I) is not None or re.search('^FORM\s*\.?$', line[3]) is not None:
            if line[3].lower().find('omitted')!=-1 or line[3].lower().find('repealed')!=-1:
                x = re.sub('\[\s*(Omitted|Repealed)\s*\.?\s*\]', '', line[3], flags=re.I).strip()
                s = regex.split(r"[\p{Pd}\.]", x)
                list_of_schedules.append(s[0].strip())
                omittedScheduleList.append([len(list_of_schedules)-1, line[3]])
            else:
                if regex.search(r"\b(SCHEDULE){e<3}\b", line[3], flags=regex.I) is not None or re.search('^FORM\s*\.?$', line[3]) is not None:
                    s = regex.split(r"[\p{Pd}\.]", line[3])
                    list_of_schedules.append(s[0].strip())
                else:
                    p1 = "[A-Z]"
                    p2 = "(?:(?=[MDCLXVI])M*(?:C[MD]|D?C{0,3})(?:X[CL]|L?X{0,3})(?:I[XV]|V?I{0,3}))"
                    mo = regex.search(r"(\b(?:APPENDIX|ANNEXURE){e<3}\b[\p{P}\s]*\b(?:"+p1+r"|"+p2+r")?\b)[\p{P}\s]*", line[3])
                    list_of_schedules.append(mo.group(1).strip())
    
    return list_of_schedules, omittedScheduleList


# ### List of Sections and Schedules

# In[17]:


list_of_sections, omittedSectionList, start_schedule_index = sections_list(Lines, actDate)
pdf_dict['Sections'] = {}


# In[18]:


list_of_schedules, omittedScheduleList = schedule_list(Lines[start_schedule_index:], actDate)


# In[19]:


# Remove all punctuation from schedules
for i, schedule in enumerate(list_of_schedules):
    list_of_schedules[i] = re.sub(r'[^\w\s]', '', schedule).strip()


# ### Extract section content:
# First create a new list from previous starting from 'BE it enacted by'

# In[20]:


start_index = None
for i, line in enumerate(Lines):
    if line[3] == actDate.strip():
        start_index = i
        break
        
new_list = copy.deepcopy(Lines[start_index:])


# In[21]:


def has_section(index, Lines, section, omittedSectionList):
    seenPunct = False
    clean_line = remove_superscript(Lines[index])
    
    if Lines[index][4] != 'BOLD':
        if section in omittedSectionList and remove_punct(clean_line).startswith(remove_punct(section[0])):    # If section is omitted or repealed
            return True
        return False
    
    else:       
        if remove_punct(clean_line).startswith(remove_punct(section[0])):
            if section in omittedSectionList:    # If section is omitted or repealed
                return True
            
            if ('Rep.' in clean_line) and (fuzz.partial_ratio(clean_line.lower(), section[1].lower())>=70 or fuzz.token_set_ratio(clean_line.lower(), section[1].lower())>=70):
                return True
            
            additionalSection = ''
            flag = False
            #seenDot = False
            for i, text_line in enumerate(Lines[index][5]):
                for j, character in enumerate(text_line):
                    if isinstance(character, LTChar):
                        if regex.search(r"[\p{Pd}\.]", character._text) is not None:
                            seenPunct = True
                        if 'bold' not in character.fontname.lower() and regex.search(r"[\p{Pd}\. ]", character._text) is None and seenPunct: #j not in dontUse:
                            content_index = j
                            obj = i
                            additionalSection += ' ' + text_line.get_text()[:content_index].strip()
                            flag = True
                            break
                else:
                    additionalSection += ' ' + text_line.get_text().strip()
                    continue
                break
            
            if flag:
                clean_text = re.sub(' +', ' ', additionalSection.strip()).strip()
                bold_part = clear_references(clean_text)
                # EDIT DISTANCE
                if fuzz.partial_ratio(bold_part.lower(), '. '.join(section).lower())>=70 or fuzz.token_set_ratio(bold_part.lower(), '. '.join(section).lower())>=70:
                    return True
                else:
                    return False
            
            else:
                sec_name = Lines[index][3]
                inc = 1
                while True:
                    additionalSection = ''
                    flag = False
                    #seenDot = False
                    for i, text_line in enumerate(Lines[index+inc][5]):
                        for j, character in enumerate(text_line):
                            if isinstance(character, LTChar):
                                if regex.search(r"[\p{Pd}\.]", character._text) is not None:
                                    seenPunct = True
                                if 'bold' not in character.fontname.lower() and regex.search(r"[\p{Pd}\. ]", character._text) is None and seenPunct: #j not in dontUse:
                                    content_index = j
                                    obj = i
                                    additionalSection += ' ' + text_line.get_text()[:content_index].strip()
                                    flag = True
                                    break
                        else:
                            additionalSection += ' ' + text_line.get_text().strip()
                            continue
                        break
                                
                    
                    if flag:
                        clean_text = re.sub(' +', ' ', additionalSection.strip()).strip()
                        sec_name = sec_name + ' ' + clean_text
                        break
                    else:
                        sec_name = sec_name + ' ' + Lines[index+inc][3]
                    inc += 1
                        
                check = clear_references(sec_name).strip()
                # EDIT DISTANCE
                if fuzz.partial_ratio(check.lower(), '. '.join(section).lower())>=70 or fuzz.token_set_ratio(check.lower(), '. '.join(section).lower())>=70:
                    return True
                else:
                    return False
        else:
            return False


# In[22]:


def find_section(index, Lines, section, omittedSectionList):
    seenPunct = False
    string = ''
    content_index = -1
    
    if section in omittedSectionList:
        x0 = Lines[index][0]
        y0 = Lines[index][1]
        string = Lines[index][3].split('.',1)[1].strip()
        jump_inc = 1
        return x0, y0, string, jump_inc
    
    if ('Rep.' in Lines[index][3]) and (fuzz.partial_ratio(Lines[index][3].lower(), section[1].lower())>=70 or fuzz.token_set_ratio(Lines[index][3].lower(), section[1].lower())>=70):
        x0 = Lines[index][0]
        y0 = Lines[index][1]
        string = Lines[index][3].split('.',1)[1].strip()
        jump_inc = 1
        return x0, y0, string, jump_inc
    
    flag = False
    for i, text_line in enumerate(Lines[index][5]):
        for j, character in enumerate(text_line):
            if isinstance(character, LTChar):
                if regex.search(r"[\p{Pd}\.]", character._text) is not None:
                    seenPunct = True
                if 'bold' not in character.fontname.lower() and regex.search(r"[\p{Pd}\. ]", character._text) is None and seenPunct: #j not in dontUse:
                    content_index = j
                    obj = i
                    flag = True
                    break
        else:
            continue
        break
                        
    if flag:
        x0 = Lines[index][0]
        y0 = Lines[index][1]
        s1 = Lines[index][5][obj].get_text()[content_index:].strip()
        if obj < len(Lines[index][5])-1:
            while obj != len(Lines[index][5])-1:
                obj += 1
                s1 += ' ' + Lines[index][5][obj].get_text().strip()
        string = re.sub(' +', ' ', s1.strip()).strip()

        jump_inc = 1
        return x0, y0, string, jump_inc
    
    else:
        x0 = Lines[index][0]
        sec_name = Lines[index][3]
        inc = 1
        while True:
            additionalSection = ''
            flag = False
            for i, text_line in enumerate(Lines[index+inc][5]):
                for j, character in enumerate(text_line):
                    if isinstance(character, LTChar):
                        if regex.search(r"[\p{Pd}\.]", character._text) is not None:
                            seenPunct = True
                        if 'bold' not in character.fontname.lower() and regex.search(r"[\p{Pd}\. ]", character._text) is None and seenPunct: #j not in dontUse:
                            content_index = j
                            obj = i
                            additionalSection += ' ' + text_line.get_text()[:content_index].strip()
                            flag = True
                            break
                else:
                    additionalSection += ' ' + text_line.get_text().strip()
                    continue
                break
                

            if flag:
                y0 = Lines[index+inc][5][obj].y0
                s1 = Lines[index+inc][5][obj].get_text()[content_index:].strip()
                if obj < len(Lines[index+inc][5])-1:
                    while obj != len(Lines[index+inc][5])-1:
                        obj += 1
                        s1 += ' ' + Lines[index+inc][5][obj].get_text().strip()
                
                clean_text = re.sub(' +', ' ', additionalSection.strip()).strip()
                sec_name = sec_name + ' ' + clean_text
                string = re.sub(' +', ' ', s1.strip()).strip()
                inc += 1
                break
            else:
                sec_name = sec_name + ' ' + Lines[index+inc][3]
            
            inc += 1
        
        jump_inc = inc
        return x0, y0, string, jump_inc


# In[23]:


def section_content(Lines, list_of_sections, omittedSectionList):
    section_dict = {}
    start_of_schedule = None
    i = 0
    
    for num, section in enumerate(list_of_sections):
        arg_list = []
        last_section = (num == len(list_of_sections)-1)
        string_indent = [-1,'']
        indent = []
        flag = False

        if last_section:
            execute = True
            #i = 0
            while i < len(Lines):
                line = Lines[i]
                if has_section(i, Lines, section, omittedSectionList) and not flag:
                    x0, y0, string, jump_inc = find_section(i, Lines, section, omittedSectionList)
                    indent.append(x0)
                    last_line_x0 = x0
                    last_line_y0 = y0
                    string_indent[0] = x0
                    string_indent[1] += string
                    flag = True
                    i = i + jump_inc
                    continue
                    
                if flag and bool(list_of_schedules):
                    if regex.search(r"\b("+list_of_schedules[0]+r"){e<3}\b", clear_references(line[3])) or (list_of_schedules[0]=='FORM' and re.search('^F\s*O\s*R\s*M$', clear_references(line[3])) is not None):
                        if len(string_indent[1].strip()) != 0:
                            level = indent.index(string_indent[0])
                            arg_list.append(Node(string_indent[1].strip(), level))
                        string_indent[0] = -1
                        string_indent[1] = ''
                        flag = False
                        execute = False
                        start_of_schedule = i
                        break                        

                if flag:
                    add_newline = ' '
                    if Lines[i-1][6] != line[6]:              # if we jump to new page in content
                        if (line[0] > last_line_x0):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= last_line_x0) and (line[0] in indent) and (re.search("^[a-z].*", line[3]) is None):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < last_line_x0:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''

                    else:
                        if (line[0] > string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < string_indent[0]:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''

                    last_line_x0 = line[0]
                    last_line_y0 = line[1]
                    string_indent[1] += add_newline + line[3]

                i = i + 1      # while loop increment

            if execute:
                level = indent.index(string_indent[0])
                arg_list.append(Node(string_indent[1], level))
                string_indent[0] = -1
                string_indent[1] = ''


        else:
            #i = 0
            while i < len(Lines):
                line = Lines[i]
                if has_section(i, Lines, section, omittedSectionList) and not flag:
                    x0, y0, string, jump_inc = find_section(i, Lines, section, omittedSectionList)
                    indent.append(x0)
                    last_line_x0 = x0
                    last_line_y0 = y0
                    string_indent[0] = x0
                    string_indent[1] += string
                    flag = True
                    i = i + jump_inc
                    continue

                if flag and has_section(i, Lines, list_of_sections[num+1], omittedSectionList):    # for the line where next section starts
                    if len(string_indent[1].strip()) != 0:
                        level = indent.index(string_indent[0])
                        arg_list.append(Node(string_indent[1].strip(), level))
                    string_indent[0] = -1
                    string_indent[1] = ''
                    flag = False
                    break

                if flag:
                    add_newline = ' '
                    if Lines[i-1][6] != line[6]:              # if we jump to new page in content
                        if (line[0] > last_line_x0):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= last_line_x0) and (line[0] in indent) and (re.search("^[a-z].*", line[3]) is None):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < last_line_x0:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''

                    else:
                        if (line[0] > string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < string_indent[0]:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            

                    last_line_x0 = line[0]
                    last_line_y0 = line[1]
                    string_indent[1] += add_newline + line[3]

                i = i + 1      # while loop increment

        global counter
        counter = [-1]
        root = Node('root', 0)
        root.add_children(arg_list)
        d = root.as_dict()[0]['contains']
        section_dict['Section '+str(section[0])+'.'] = {'heading': section[1], 'paragraphs': copy.deepcopy(d)}
        
    return section_dict, start_of_schedule


# In[24]:


pdf_dict['Sections'], start_of_schedule = section_content(new_list, list_of_sections, omittedSectionList)


# ### Schedule Content

# In[25]:


def schedule_content(Lines, list_of_schedules, omittedScheduleList):
    schedule_dict = {}
    i = 0
    
    for num, schedule in enumerate(list_of_schedules):
        flag = False
        string = ''
        last_schedule = (num == len(list_of_schedules)-1)
        arg_list = []
        string_indent = [-1,'']
        indent = []

        if last_schedule:
            while i < len(Lines):
                line = Lines[i]
                if (regex.search(r"\b("+schedule+r"){e<3}\b", clear_references(line[3])) or (schedule=='FORM' and re.search('^F\s*O\s*R\s*M$', clear_references(line[3])) is not None)) and not flag:
                    begin = line[3].find(schedule) + len(schedule)
                    string = line[3]
                    indent.append(line[0])
                    last_line_x0 = line[0]
                    last_line_y0 = line[1]
                    string_indent[0] = line[0]
                    string_indent[1] += string
                    flag = True
                    i = i + 1
                    continue

                if flag:
                    add_newline = ' '
                    if Lines[i-1][6] != line[6]:              # if we jump to new page in content
                        if (line[0] > last_line_x0):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= last_line_x0) and (line[0] in indent) and (re.search("^[a-z].*", line[3]) is None):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < last_line_x0:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''

                    else:
                        if (line[0] > string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):     # CHANGED
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < string_indent[0]:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''

                    last_line_x0 = line[0]
                    last_line_y0 = line[1]
                    string_indent[1] += add_newline + line[3]
                    
                i = i + 1
                    

            if len(string_indent[1].strip()) != 0:
                level = indent.index(string_indent[0])
                arg_list.append(Node(string_indent[1].strip(), level))
            string_indent[0] = -1
            string_indent[1] = '' 


        else:
            while i < len(Lines):
                line = Lines[i]
                if regex.search(r"\b("+schedule+r"){e<3}\b", clear_references(line[3])) and not flag:
                    begin = line[3].find(schedule) + len(schedule)
                    string = line[3]
                    indent.append(line[0])
                    last_line_x0 = line[0]
                    last_line_y0 = line[1]
                    string_indent[0] = line[0]
                    string_indent[1] += string
                    flag = True
                    i = i + 1
                    continue

                if flag and regex.search(r"\b("+list_of_schedules[num+1]+r"){e<3}\b", clear_references(line[3])):
                    if len(string_indent[1].strip()) != 0:
                        level = indent.index(string_indent[0])
                        arg_list.append(Node(string_indent[1].strip(), level))
                    string_indent[0] = -1
                    string_indent[1] = ''
                    flag = False
                    break

                if flag:
                    add_newline = ' '
                    if Lines[i-1][6] != line[6]:              # if we jump to new page in content
                        if (line[0] > last_line_x0):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= last_line_x0) and (line[0] in indent) and (re.search("^[a-z].*", line[3]) is None):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < last_line_x0:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''

                    else:
                        if (line[0] > string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            if line[0] not in indent:
                                indent.append(line[0])

                        if (line[0] <= string_indent[0]) and (round(last_line_y0 - line[2],2)> 4):     # CHANGED
                            if len(string_indent[1].strip()) != 0:
                                level = indent.index(string_indent[0])
                                arg_list.append(Node(string_indent[1].strip(), level))
                            if line[0] < string_indent[0]:
                                while bool(indent) and indent[-1] > line[0]:
                                    indent.pop()
                                if line[0] not in indent:
                                    indent.append(line[0])
                            string_indent[0] = line[0]
                            string_indent[1] = ''
                            

                    last_line_x0 = line[0]
                    last_line_y0 = line[1]
                    string_indent[1] += add_newline + line[3]
                    
                i = i + 1

        
        global counter
        counter = [-1]
        root = Node('root', 0)
        root.add_children(arg_list)
        d = root.as_dict()[0]['contains']
        isOmitted = False
        for item in omittedScheduleList:
            if num == item[0]:
                schedule_dict[item[1]] = copy.deepcopy(d)
                isOmitted = True
                break
        if not isOmitted:
            schedule_dict[schedule] = copy.deepcopy(d)
    
    return schedule_dict


# In[26]:


pdf_dict['Schedule'] = {}
pdf_dict['Annexure'] = {}
pdf_dict['Appendix'] = {}
pdf_dict['Forms'] = {}

if bool(list_of_schedules): 
    schedule_dict = schedule_content(new_list[start_of_schedule:], list_of_schedules, omittedScheduleList)
    
    for key in schedule_dict:
        if regex.search(r"\b(SCHEDULE){e<3}\b", key, flags=regex.I) is not None:
            pdf_dict['Schedule'][key] = schedule_dict[key]

        elif regex.search(r"\b(ANNEXURE){e<3}\b", key, flags=regex.I) is not None:
            pdf_dict['Annexure'][key] = schedule_dict[key]

        elif regex.search(r"\b(APPENDIX){e<3}\b", key, flags=regex.I) is not None:
            pdf_dict['Appendix'][key] = schedule_dict[key]

        elif re.search('^FORM\s*\.?$', key) is not None:
            pdf_dict['Forms'][key] = schedule_dict[key]


# ### Extract Footnotes

# In[27]:


def extract_footnotes(example_file):
    import re
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextBoxHorizontal, LTChar, LTRect

    string = ''
    flag = False
    footnotes = {}
    temp_list = []

    for page_layout in extract_pages(example_file):
        d = {}
        para_id = 0
        
        for element in page_layout:
            if isinstance(element, LTRect) and (round(element.width,4) in (140.16,144,144.02,144.05)) and int(element.height)==0:
                LTFootnote_y0 = element.y0
                flag = True
                break
            if isinstance(element, LTLine) and element.y0<150 and element.width>0 and element.width<200 and element.x0>0 and element.x0<100:
                LTFootnote_y0 = element.y0
                flag = True
                break
        if flag:
            for element in page_layout:
                if isinstance(element, LTTextBoxHorizontal) and element.y0 < LTFootnote_y0:
                    for text_line in element:
                        if text_line.y0 < LTFootnote_y0:
                            if text_line.get_text().strip() == str(page_layout.pageid) or re.search("^_*$", text_line.get_text().strip()) is not None:
                                continue
                            else:
                                temp_list.append(text_line)

            def get_my_key(obj):
                return obj.y0
            temp_list.sort(reverse=True, key=get_my_key)

            for obj in temp_list:
                if re.search("^[0-9]\..*", obj.get_text()) is not None:
                    if string.strip() != '':
                        d[para_id] = string.strip()
                        para_id += 1
                        string = ''
                    string += obj.get_text().strip()
                else:
                    string += obj.get_text().strip()
            
            if string.strip() != '':
                d[para_id] = string.strip()
                para_id += 1
                string = ''
            if bool(d):
                footnotes["Page "+ str(page_layout.pageid)] = d
            flag = False
            temp_list.clear()

    return footnotes


# In[28]:


footnotes = extract_footnotes(example_file)
pdf_dict['Footnotes'] = copy.deepcopy(footnotes)


# ### Create a json format using json.dumps() and write it to a file

# In[29]:


import json

json_object = json.dumps(pdf_dict, indent = 4)   

f = open("check.json","w")
f.write(json_object)
f.close()

