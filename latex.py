import os
import re
import json

from typing import List

class LatexSubsection:
    title: str
    content: str

    def __init__(self, title, content):
        self.title = title
        self.content = content

class LatexSection:
    title: str
    subsections: List[LatexSubsection]

    def __init__(self, title: str, subsections: List[LatexSubsection]):
        self.title = title
        self.subsections = subsections

def read_latex_data(data: str):
    # define a pattern for sections
    section_pattern = r"\\section\{(.*?)\}((\\section\{.*?\}|\\end\{document\})|$)"
    # define a pattern for subsections
    subsection_pattern = r"\\subsection\{(.*?)\}((\\subsection\{.*?\}|\\section\{.*?\}|\\end\{document\})|$)"

    sections = []
    for section_match in re.findall(section_pattern, data, re.DOTALL):
        subsections = []
        for subsection_match in re.findall(subsection_pattern, section[1], re.DOTALL):
            subsection = LatexSubsection(subsection_match[0], subsection_match[1])
            subsections.append(subsection)

        sections.append(LatexSection(section_match[0], subsections))

    print(f'Found {len(sections)} sections in LaTex file')
    return sections