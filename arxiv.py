import os

import openai

from bot import Researcher
from util import save_file

class ArxivGPT:
    def __init__(self, 
            api_key: str
        ):
        openai.api_key = api_key
        self.researcher = Researcher()
        self.completions = []

    def read_paper(self, paper_id: str, max_tokens: int):
        def to_snake_case(string):
            string = string.lower().replace(' ', '_').replace('-', '_')
            return ''.join(['_' + i.lower() if i.isupper() else i for i in string]).lstrip('_')
        
        summary = self.researcher.read_paper(paper_id, max_tokens)
        if summary == None:
            print("Error occured, exiting")
            return None
        print("Saving completions to file")
        self.researcher.save_completions(f'arxiv_{to_snake_case(summary.title)}_paper')
        print(f'Total Tokens Used: {self.researcher.total_tokens}')

        print('Saving Summary')
        if not os.path.exists('summaries'):
            os.mkdir('summaries')

        summary_text = f'{summary.title}\n\n{summary.text}'
        
        save_file(f'summaries/{paper_id}_summary.txt', summary_text)