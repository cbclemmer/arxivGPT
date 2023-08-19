import os
import re
import json

from typing import List

class LatexSubsection:
    title: str
    content: str

    def __init__(self, title: str, content: str = ''):
        self.title = title
        self.content = content

    def to_json(self):
        return {
            "title": self.title,
            "content": self.content
        }

class LatexSection:
    title: str
    subsections: List[LatexSubsection]

    def __init__(self, title: str, subsections: List[LatexSubsection] = []):
        self.title = title
        self.subsections = subsections

    def to_json(self):
        return {
            "title": self.title,
            "subsections": [sub.to_json() for sub in self.subsections]
        }

class LatexParser:
    def __init__(self, text: str):
        self.text = text
        self.sections = []
        self.current_section = LatexSection('Begin Document')
        self.current_sub_section = LatexSubsection('Begin Document')
        self.skipping = False
        self.parse()

    def parse_command(self, command, command_data):
        # print(f'COMMAND: {command} - {command_data}')
        if command == 'section':
            if self.current_sub_section != None and self.current_sub_section.content.strip() != '':
                self.current_section.subsections.append(self.current_sub_section)
            if self.current_section != None and len(self.current_section.subsections) > 0:
                self.sections.append(self.current_section)
            self.current_section = LatexSection(command_data)
            self.current_sub_section = LatexSubsection('Begin Section', '')
        if command == 'subsection':
            if self.current_sub_section is not None and self.current_sub_section.content.strip() != '':
                self.current_section.subsections.append(self.current_sub_section)
            self.current_sub_section = LatexSubsection(command_data)
        if command == 'begin':
            self.skipping = command_data != 'document'
        if command == 'end':
            self.skipping = False
        if (command == 'textbf' or command == 'emph' or command == 'textit') and not self.skipping and self.current_sub_section != None:
            self.current_sub_section.content += command_data

    def parse(self):
        command = None
        command_data = None
        last_c = ''

        for c in self.text:
            if c == '\\' and command is None:
                command = ''
                continue
            if command is not None:
                if c == '{':
                    command_data = ''
                    continue
                if c == '}' or ((c == ' ' or c == '\n') and command_data is None):
                    self.parse_command(command, command_data)
                    command = None
                    command_data = None
                    continue
                if command_data is None:
                    command += c
                else:
                    command_data += c
                continue
            if not self.skipping and self.current_sub_section != None:
                if last_c == '\n' and c == '\n':
                    continue
                self.current_sub_section.content += c
            last_c = c
        self.current_section.subsections.append(self.current_sub_section)
        self.sections.append(self.current_section)

    def to_json(self):
        return [sec.to_json() for sec in self.sections]

def read_latex_data(data: str):
    parser = LatexParser(data)

    print(f'Found {len(parser.sections)} sections in LaTex file')
    return parser.sections