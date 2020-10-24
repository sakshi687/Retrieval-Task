## Introduction
Source:  https://www.indiacode.nic.in/ 

Under Central Acts there were 856 acts presented in the form of pdfs. The aim was to convert these pdfs into JSON format to have access to structured data.

Upon inspection each pdf seemed to have - Act Title, Act ID, Enactment Date and Act Definition.

Furthermore, these pdfs can be broadly categorized into four patterns which are
* *Pattern No. 1*: Sections
* *Pattern No. 2*: Chapters (that may or may not have subheadings) containing Sections
* *Pattern No. 3*: Chapters without explicitly mentioning the word CHAPTER but are subheadings from above pattern containing Sections. (i.e. Headings containing Sections)
* *Pattern No. 4*: Parts (that may or may not have subheadings) containing Sections

Apart from this, these pdfs may have Schedules, Annexures, Appendix and Forms.

All the footnotes in a pdf have been extracted separately so that they do not get merged with the section content.

## Tool Used:
PDFMiner: This required PDFMiner which is a text extraction tool for PDF documents. It analyzes the pdf based on its layout and provides detailed information of each layout element (LTPage, LTRect, LTLine etc.).


## Fields In Output JSON:

**1. Act Title**: this field is a string that contains title of the Act

**1. Act ID**: this field is a string that contains Act ID

**1. Enactment Date**: this field is a string that contains enactment date of the Act
 
1. **Act Definition**: the act definition is split into paragraphs and each paragraph is numbered starting from zero. This field is a dictionary with *key* = paragraph number, *value* = paragraph (refer to Point 8b).

1. **Chapters/Parts**: this field is a dictionary with *key* = number starting from zero, *value* =

		   "0": {
			"ID": "CHAPTER I",
			"Name": "PROVISIONS APPLICABLE TO INSURERS",
			"Sections": {}
			"Subheadings": [
			       {
				   "Name": "INVESTMENT, LOANS AND MANAGEMENT",
				    "Sections": {}
				},
				{...}
			  ]
			}


1. **Chapter/Part ID**: this field is a string that generally contains for e.g. CHAPTER IV, PART I depending upon whether the pdf belongs to Pattern No. 2 or Pattern No. 4. If the Chapter/Part is omitted or repealed then the ID will contain “[Repealed]” or “[Omitted]”. If the pdf belongs to Pattern No. 3 then this field won’t be present in Chapters field.

1. **Chapter/Part Name**: this field is a string that contains chapter or part name unless the Chapter/Part is omitted or repealed then this field will be empty.

1. **Sections**: this field is a dictionary that contains sections with key as "Section 1", "Section 4A", "Section 19-H" etc. and value is again a dictionary that contains
	**1. heading**: this field is a string and contains the section heading
	1. **paragraphs**: this field is a dictionary with *key* = paragraph number starting from zero, *value* = paragraph. If the paragraph has nested indentation this field can then further contain
	
		1. text: this field is string which contains the paragraph preceding the indentation
		1. contains: this field is again paragraph (refer to point 8b)

1. **Subheadings**: this field is optional and is contained within Chapters/Parts field and is a list of dictionary elements that contains
	1. Name: the name of subheading
	1. Sections: (refer to point 8)

1. **Schedule/Annexure/Appendix/Forms**: this field is a dictionary that can be empty if there are no schedules or appendix in the pdf.

1. **Footnotes**: this field is a dictionary with *key* = Page No. of the pdf and *value* = paragraphs. It can be empty if there are no footnotes in a pdf


## Accuracy:

* **Act Title, Act ID, Enactment Date and Act Definition**:
	These can be identified with 100% accuracy

* **Section heading**:
	If a Section has multiple headings under same section number only first heading is recorded. Otherwise the section name can be identified perfectly with accuracy of 100%

* **Section paragraphs**:
	The start of section content is not accurate because we mark the beginning of section content from the point where characters become non-bold which can sometimes lead to part of section heading being included in section content. Also, sometimes in the section content paragraph change is not detected because of irregular line gap. This leads to paragraphs getting merged or nested differently but there is no information loss. Overall, the accuracy is 95%.

* **Subheadings in Chapter/Parts pattern**:
	Not able to identify some of the subheadings in Chapters and Parts as they get merged with Chapter name or Part name.



## Points To Review Later:
* Handling tables in pdfs
* Handling forms in pdfs
* Centered text in sections or schedules messes with the formatting
* Line gap that identifies new paragraphs sometimes not consistent across a pdf
* Adding some kind of reference link to the Footnotes
* In table of content if a Section has multiple headings only one heading is recorded. For e.g. 
	     1. Short title.
		Extent of Act.
  This will be recorded as just ‘Short title.’
