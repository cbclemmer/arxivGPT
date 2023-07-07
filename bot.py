import io
import os
from typing import List, Tuple

import PyPDF2
import requests
from bs4 import BeautifulSoup

from gpt import GptChat
from util import save_file
from objects import Conversation, Prompt, Summary

class Bot(GptChat):
    conversations: List[Conversation]

    def __init__(self, prompt_file: str):
        super().__init__(prompt_file)
        self.completions = []

    def complete_promts(self, prompts: List[Prompt]) -> List[Summary]:
        summaries = []
        for prompt in prompts:
            print('\nPost:')
            print(prompt.url)

            self.reset_chat()
            summary = self.send(prompt.text)
            summaries.append(Summary(prompt.title, prompt.url, summary))
            
            print(summary)
            print('\n\n')

        self.reset_chat()
        return summaries
    
class ReaserchSummarizer(Bot):
    def __init__(self):
        super().__init__('research_summarizer')

    def summarize_chunk_list(self, overall_summary = '', list = [], note = ''):
        if len(list) == 0:
            return ''
        self.reset_chat()
        print('Creating overall summary:')
        if len(note) > 0:
            self.add_message('Please keep this note in mind:\n' + note, 'user')
            self.add_message('Ok, I\' keep that in mind', 'assistant')
        if len(overall_summary) > 0:
            print(f'Overall summary is {len(self.encoding.encode(overall_summary))} tokens')
            self.add_message('What is the summary overall?', 'user')
            self.add_message(overall_summary, 'assistant')
        self.add_message('Ok, I\'m now going to give you the new notes', 'user')
        self.add_message('Ok, I\'m ready for the new notes', 'assistant')
        total_summary_tokens = 0
        for summary in list:
            current_summary_tokens = len(self.encoding.encode(summary))
            print(f'Summary is {current_summary_tokens} tokens')
            total_summary_tokens += current_summary_tokens
            self.add_message(summary, 'user')
            self.add_message('Ok, I\'m ready for the next note', 'assistant')
        print(f'All Summaries are {total_summary_tokens} tokens')
        return self.send('That is all the summaries, what is the new overall summary?', 700)

class Researcher(Bot):
    def __init__(self):
        super().__init__('researcher')
        self.summarizer = ReaserchSummarizer()

    # Returns (Title, Abstract)
    def get_abstract(self, paper_id: str) -> Tuple[str, str]:
        abs_url = f'https://arxiv.org/abs/{paper_id}'
        response = requests.get(abs_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        abstract_elem = soup.find('blockquote', {'class': 'abstract'})
        return (soup.title.string, abstract_elem.text)
    
    # returns (text, num_pages)
    def get_paper_text(self, paper_id: str) -> Tuple[str, str]:
        pdf_url = f'https://arxiv.org/pdf/{paper_id}.pdf'
        response = requests.get(pdf_url)
        if response.status_code != 200:
            print("Could not find pdf for paper")
            return None
        paper_file_name = paper_id.replace('.', '') + '.pdf'
        if not os.path.exists(paper_file_name):
            if not os.path.exists('papers'):
                os.mkdir('papers')
            with open('papers/' + paper_file_name, 'wb') as f:
                f.write(response.content)
        pdfReader = PyPDF2.PdfReader(io.BytesIO(response.content))
        text = ''
        for page_num in range(0, len(pdfReader.pages)):
            page = pdfReader.pages[page_num].extract_text()
            text += ' ' + page
        return (text,  len(pdfReader.pages))

    def read_paper(self, paper_id: str, max_tokens: int = 30000, chunk_size: int = 2500) -> Summary | None:
        (title, abstract) = self.get_abstract(paper_id)
        print(f'Title: {title}')
        print(abstract)

        should_read = input('Read paper?: ')
        if should_read.lower() != 'yes':
            return None
        print('What should I keep in mind while reading the paper? (leave blank if no notes)')
        notes = input('Notes: ')

        print("Downloading pdf")
        (text, num_pages) = self.get_paper_text(paper_id)
        tokens = self.encoding.encode(text) 
        print(f"Paper has {num_pages} pages and {len(tokens)} total tokens")

        if len(tokens) > max_tokens:
            print(f'Token count over read limit, removing {len(tokens) - max_tokens} tokens')
            print('Consider raising the maximum read tokens')
            tokens = tokens[:max_tokens]
            if input('Continue?(Y/n): ') != 'Y':
                return None

        first = False
        processed_tokens = 0
        summary_list = []
        last_summary = ''
        overall_summary = ''
        log = f'{title} Reading Log\n'
        while len(tokens) > 0:
            chunk = tokens[:chunk_size]
            tokens = tokens[chunk_size:]
            last_summary = self.read_chunk(overall_summary, chunk, first, notes)
            summary_list.append(last_summary)

            log += f'Chunk:\n{self.encoding.decode(chunk)}\nSummary:\n{last_summary}\n\n\n'

            if len(summary_list) > 4:
                summary_list = summary_list[1:5]
            if len(summary_list) > 1:
                overall_summary = self.summarizer.summarize_chunk_list(overall_summary, summary_list)
            else:
                overall_summary = last_summary
            print(f'\n\n\nOverall Summary:{overall_summary}\n\n\n')
            print(f'\n\n\nCurrent Summary:{last_summary}\n\n\n')
            processed_tokens += chunk_size
            print(f"Processed {processed_tokens} of {len(tokens)} tokens")
        self.reset_chat()
        
        log += f'Overall Summary:\n{overall_summary}'

        print('Saving Log')
        if not os.path.exists('logs'):
            os.mkdir('logs')
        save_file(f'logs/arxiv_{paper_id}.txt', log)

        pdf_url = f'https://arxiv.org/pdf/{paper_id}.pdf'
        return Summary(title, overall_summary, pdf_url)
    
    def read_chunk(self, current_summary: str, chunk: List[int], first: bool, notes: str) -> str:
        text = self.encoding.decode(chunk)
        self.reset_chat()
        if notes != '':
            self.add_message(f'Keep in mind this note:\n{notes}', 'user')
            self.add_message('Ok, I\'ll keep that in mind', 'assistant')
        if first:
            first = False
        else:
            self.add_message("What is the summary so far?", "user")
            self.add_message(current_summary, "assistant")
            self.add_message("Are you ready for the next page?", "user")
            self.add_message("Yes, please provide the next page of text", "assistant")
        return self.send(text, 500)