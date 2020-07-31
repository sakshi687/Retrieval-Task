#!/usr/bin/env python
# coding: utf-8

# ### Use pdfplumber to convert pdf to text

# In[1]:


import pdfplumber
import re

document = ''
with pdfplumber.open(r'A1991-11.pdf') as pdf:
    list_of_pages = pdf.pages
    for i in range(len(list_of_pages)):
        current_page = pdf.pages[i].extract_text().strip()
        current_page = "\n".join(current_page.split("\n")[0:-1])    #Remove last line which is the page number
        current_page = current_page.strip() + '\n\n'
        document += current_page
document = document.encode("ascii", "ignore").decode()
document = re.sub(' +', ' ', document).strip()


# In[2]:


print(document)


# ### Split the document by newline and create a List

# In[3]:


Lines = document.split('\n')

for i, line in enumerate(Lines):
    Lines[i] = line.strip()


# ### Extract Act ID and Act Title

# In[4]:


dict = {}


#Act ID
for line in Lines:
    if re.match("^ACT\s+NO.*", line.strip()):
        dict["Act ID"] = line.strip()
        break


#Act Title
str1 = ''
for line in Lines:
    if re.match("^_+$", line.strip()):
        str1 = str1.strip()
        break
    str1 += line.strip() + ' '
dict["Act Title"] = str1


# In[5]:


dict


# ### Extract Act Definition

# In[6]:


#Act Definition
str2 = ''
flag = False
for line in Lines:
    if re.match("^an\s+act\s+to.*", line.lower()):
        flag = True
    if re.match("^be\s+it\s+enacted\s+by.*", line.lower()):
        str2 = str2.strip()
        flag = False
        break
    if flag == True:
        str2 += line.strip() + ' '
dict["Act Definition"] = str2


# In[7]:


dict["Act Definition"]


# ### Add to dictionary the list of chapters and sections

# In[8]:


list_of_chapters = []
list_of_sections = []
flag = False
count = 0

dict['Chapters'] = {}

for i, line in enumerate(Lines):
    if re.match("^chapter.*", line.lower()):
        key1 = line.strip()
        chap_name = Lines[i+1].strip()
        
        inc = 2
        while True:
            if re.match("^[0-9]+\.\s*[a-z].*", Lines[i+inc].lower()):
                break
            elif Lines[i+inc].strip() == 'SECTIONS':
                inc += 1
                continue
            else:
                chap_name = chap_name + ' ' + Lines[i+inc].strip()
                inc += 1

        chap_name = chap_name.strip()
        list_of_chapters.append(chap_name)
        dict['Chapters'][key1] = {'name': chap_name, 'Sections': {}}
        
    if re.match("^be\s+it\s+enacted\s+by.*", line.lower()):
        count = 1
        break
    
    if re.match("^[0-9]+\.\s*[a-z].*", line.lower()):
        mo = re.search(r"(([0-9]+)\.\s*([a-zA-Z].*))", line)
        sec_name = mo.group(3).strip()
        
        inc = 1
        while True:
            if sec_name[-1]!='.':
                sec_name = sec_name + ' ' + Lines[i+inc].strip()
                inc += 1
            else:
                break
        
        list_of_sections.append(sec_name)
        key2 = 'Section ' + mo.group(2).strip() + '.'
        dict['Chapters'][key1]['Sections'][key2] = {'name': sec_name, 'content': ''}


# In[9]:


dict


# ### Create a new document for the purpose of extracting content: 
# We need to create a new document without any newlines so we can detect name of sections that span in multiple lines and hence extract their content

# In[10]:


start_index = -1
for i, line in enumerate(Lines):
    if re.search(r"be\s+it\s+enacted\s+by.*", line.lower())!= None:
        start_index = i
        break

new_list = Lines[start_index:]

for i, line in enumerate(new_list):
    if re.search(r"THE\sSCHEDULE", line.strip())!= None:
        end_index = i
        new_list = new_list[:end_index]
        break

index = 0
while index < len(new_list):
    # check if CHAPTER or its name is in the line
    if re.search(r"^(\d+\[)?\s*[A-Z\s]+$", new_list[index].strip())!= None:
        # remove it
        del(new_list[index])
    else:
        index += 1

new_doc = ' '.join(new_list)


# In[11]:


list_of_sections


# In[12]:


contents = []

for i, section in enumerate(list_of_sections):
    position1 = (new_doc.find(section))
    begin = position1 + len(section)
    if i == len(list_of_sections)-1:
        x = new_doc[begin:]
        contents.append(x.strip())
    else:
        pattern = r"[0-9]+\.\s*" + list_of_sections[i+1]
        if re.search(pattern, new_doc):
            end = re.search(pattern, new_doc).start()
            x = new_doc[begin:end]
            contents.append(x.strip())
        else:
            print(section + "    PATTERN NOT FOUND!!!")        


# In[13]:


contents[0]


# ### Add the content of each section to the dictionary

# In[14]:


index = 0
for i in dict['Chapters'].keys():
    for j in dict['Chapters'][i]['Sections'].keys():
        dict['Chapters'][i]['Sections'][j]['content'] = contents[index]
        index += 1


# In[15]:


dict


# ### Create a json format using json.dumps() and write it to a file

# In[16]:


import json

json_object = json.dumps(dict, indent = 4)   

f = open("FileToJSON.json","w")
f.write(json_object)
f.close()


# In[ ]:




