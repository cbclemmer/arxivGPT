import io
import os
import tarfile
import gzip
from typing import List, Tuple

import PyPDF2
import requests
from bs4 import BeautifulSoup

from gpt import GptChat
from util import save_file
from objects import Conversation, Prompt, Summary
from latex import LatexSection
import arxiv

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
        return self.send('That is all the summaries, what is the new overall summary?', 200)

class Researcher(Bot):
    def __init__(self):
        super().__init__('researcher')
        self.summarizer = ReaserchSummarizer()

    def read_paper_sections(self, paper_id: str, max_tokens: int, chunk_size: int, sections: List[LatexSection], notes: str):
        log = ''
        summary = ''
        for section in sections:
            section_text = ''
            for subsection in section.subsections:
                section_text += f'### {subsection.title}\n{subsection.content}'
            print(f'Reading Section: {section.title}')
            (section_summary, section_log) = self.read_text(section.title, chunk_size, section_text, notes)
            summary += f'\n\n### {section.title}\n{section_summary}'
            log += f'#### {section.title}\n{section_log}'

        self.save_log(paper_id, log)

        pdf_url = f'https://arxiv.org/pdf/{paper_id}.pdf'
        return Summary(paper_id, summary, pdf_url)

    def read_text(self, title: str, chunk_size: int, text: str, notes: str):
        first = False
        processed_tokens = 0
        summary_list = []
        last_summary = ''
        overall_summary = ''
        log = f'{title} Reading Log\n'
        tokens = self.encoding.encode(text)
        while len(tokens) > 0:
            chunk = tokens[:chunk_size]
            tokens = tokens[chunk_size:]
            last_summary = self.read_chunk(overall_summary, chunk, first, notes)
            summary_list.append(last_summary)

            log += f'Chunk:\n{self.encoding.decode(chunk)}\nSummary:\n{last_summary}\n\n\n'

            if len(summary_list) > 4:
                summary_list = summary_list[1:5]
            overall_summary = self.summarizer.summarize_chunk_list(overall_summary, summary_list)
            print(f'\n\n\nOverall Summary:{overall_summary}\n\n\n')
            print(f'\n\n\nCurrent Summary:{last_summary}\n\n\n')
            processed_tokens += chunk_size
            print(f"Processed {processed_tokens} of {len(tokens)} tokens")
        self.reset_chat()
        
        log += f'Overall Summary:\n{overall_summary}'

        return (overall_summary, log)

    def save_log(self, paper_id: str, log: str):
        print('Saving Log')
        if not os.path.exists('logs'):
            os.mkdir('logs')
        save_file(f'logs/arxiv_{paper_id}.txt', log)

    def read_paper_text(self, paper_id: str, chunk_size: int, text: str):
        (overall_summary, log) = self.read_text(paper_id, chunk_size, text)
        print(f'Used {self.total_tokens + self.summarizer.total_tokens} tokens in total')

        self.save_log(paper_id, log)

        pdf_url = f'https://arxiv.org/pdf/{paper_id}.pdf'
        return Summary(title, overall_summary, pdf_url)

    def read_paper(self, paper_id: str, max_tokens: int = 30000, chunk_size: int = 2500) -> Summary | None:
        (title, abstract) = arxiv.get_abstract(paper_id)
        print(f'Title: {title}')
        print(abstract)

        should_read = input('Read paper?: ')
        if should_read.lower() != 'yes':
            return None
        print('What should I keep in mind while reading the paper? (leave blank if no notes)')
        notes = input('Notes: ')

        (text, num_pages) = arxiv.get_paper_text(paper_id)
        tokens = self.encoding.encode(text)
        print(f"Paper has {num_pages} pages and {len(tokens)} total tokens")
        if len(tokens) > max_tokens:
            print(f'Token count over read limit, removing {len(tokens) - max_tokens} tokens')
            print('Consider raising the maximum read tokens')
            tokens = tokens[:max_tokens]
            if input('Continue with truncated data?(Y/n): ') != 'Y':
                return None
        print('Looking for LaTex source code for paper...')
        sections = arxiv.get_sections(paper_id)
        summary = None
        if sections is None:
            print('Could not find source code. Summarizing raw pdf text')
            summary = self.read_paper_text(paper_id, chunk_size, text)
        else:
            summary = self.read_paper_sections(paper_id, max_tokens, chunk_size, sections, notes)
        return summary
    
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