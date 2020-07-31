#!/usr/bin/env python
# coding: utf-8

# ### Use pdfplumber to convert pdf to text

# In[1]:


import pdfplumber
import re

document = ''
with pdfplumber.open(r'A2014_40.pdf') as pdf:
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


# ### Add to dictionary the list of sections

# In[8]:


list_of_sections = []
flag = False
dict['Sections'] = {}

for line in Lines:
    if line.strip() == 'SECTIONS':
        flag = True
    if re.match("^be\s+it\s+enacted\s+by.*", line.lower()):
        break
    if flag:
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
            
            key = 'Section ' + mo.group(2).strip() + '.'
            dict['Sections'][key] = {'name': sec_name, 'content': ''}


# In[9]:


dict


# ### Create a new document for the purpose of extracting content: 
# We need to create a new document without any newlines so we can detect name of sections that span in multiple lines and hence extract their content

# In[10]:


for i, line in enumerate(Lines):
    if re.search(r"be\s+it\s+enacted\s+by.*", line.lower())!= None:
        start_index = i
        break
        
new_list = Lines[start_index:]

new_doc = ' '.join(new_list)


# In[17]:


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
            print("Pattern Not found!!!")
        


# ### Add the content of each section to the dictionary

# In[19]:


index = 0
for i in dict['Sections'].keys():
    dict['Sections'][i]['content'] = contents[index]
    index += 1


# In[20]:


dict


# ### Create a json format using json.dumps() and write it to a file

# In[21]:


import json

json_object = json.dumps(dict, indent = 4)   

f = open("FileToJSON.json","w")
f.write(json_object)
f.close()


# In[ ]:




