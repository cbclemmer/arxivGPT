import os
import sys
import json

import openai

from bot import Researcher
from util import save_file
from generate_html import generate_html

class ArxivGPT:
    def __init__(self, 
            api_key: str
        ):
        openai.api_key = api_key
        self.researcher = Researcher()
        self.completions = []

    def read_paper(self, paper_id: str, max_tokens: int):
        def to_snake_case(string):
            string = string.lower().replace(' ', '_').replace('-', '_').replace(',', '')
            return ''.join(['_' + i.lower() if i.isupper() else i for i in string]).lstrip('_')
        
        summary = self.researcher.read_paper(paper_id, max_tokens)
        if summary == None:
            print("Error occured, exiting")
            return None
        print("Saving completions to file")
        completion_file = f'arxiv_{to_snake_case(summary.title)}_paper'
        self.researcher.save_completions(completion_file)
        if not os.path.exists('html_logs'):
            os.mkdir('html_logs')
        html = generate_html(summary.title, completion_file)
        save_file(f'html_logs/{completion_file}.html', html)

        print(f'Total Tokens Used: {self.researcher.total_tokens}')

        print('Saving Summary')
        if not os.path.exists('summaries'):
            os.mkdir('summaries')

        summary_text = f'{summary.title}\n\n{summary.text}'
        
        save_file(f'summaries/{paper_id}_summary.txt', summary_text)

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

paper_id = ''
if len(sys.argv) > 1:
    paper_id = sys.argv[1]
else:
    raise "Not enough arguments must be in form python main.py [paper_id]\nwhere paper_id is the papers id found in the arvix url"

config = json.loads(open_file('config.json'))

max_tokens = 30000
if 'max_tokens' in config:
    max_tokens = int(config['max_tokens'])

ArxivGPT(config["openai_key"]).read_paper(paper_id, max_tokens)