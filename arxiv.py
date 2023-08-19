import io
import os
import tarfile
import gzip
import shutil
from typing import List, Tuple

import PyPDF2
import requests
from bs4 import BeautifulSoup

from gpt import GptChat
from util import save_file, open_file
from objects import Conversation, Prompt, Summary
from latex import read_latex_data

# Returns (Title, Abstract)
def get_abstract(paper_id: str) -> Tuple[str, str]:
    abs_url = f'https://arxiv.org/abs/{paper_id}'
    response = requests.get(abs_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    abstract_elem = soup.find('blockquote', {'class': 'abstract'})
    return (soup.title.string, abstract_elem.text)

# returns (text, num_pages)
def get_paper_text(paper_id: str) -> Tuple[str, str]:
    paper_file_name = 'papers/' + paper_id.replace('.', '') + '.pdf'
    paper_data = None
    if os.path.exists(paper_file_name):
        print('Found paper file, reading contents')
        with open(paper_file_name, 'rb') as f:
            paper_data = f.read()
    else:
        print("Downloading pdf")
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
            paper_data = response.content
    pdfReader = PyPDF2.PdfReader(io.BytesIO(paper_data))
    text = ''
    for page_num in range(0, len(pdfReader.pages)):
        page = pdfReader.pages[page_num].extract_text()
        text += ' ' + page
    return (text, len(pdfReader.pages))

def get_sections(paper_id: str):
    source_file_name = 'source/' + paper_id.replace('.', '')
    source_data = None
    if os.path.exists(source_file_name):
        print('Found paper source in files, reading data...')
        with open(source_file_name, 'rb') as f:
            source_data = f.read()
    else:
        print('Attempting to download source')
        url = f'https://arxiv.org/e-print/{paper_id}'
        response = requests.get(url)
        if response.status_code == 404:
            print(f'Error reading source: recieved 404 for {url}')
            return None
        if response.status_code != 200:
            raise Exception(f'Error downloading source code for paper {paper_id}\n{response.content.decode()}')
        print('Found paper source code, parsing file')
        if not os.path.exists('source'):
            os.mkdir('source')
        with open(source_file_name, 'wb') as f:
            f.write(response.content)
        source_data = response.content
    if os.path.exists('tmp'):
        shutil.rmtree('tmp')
    os.mkdir('tmp')
    try:
        tar_file = None
        if not tarfile.is_tarfile(source_file_name):
            with gzip.open(source_file_name) as f:
                gzip_file = f.read()
                tar_file = gzip.decompress(gzip_file)
                os.remove(source_file_name)
                with open(source_file_name, 'wb') as f:
                    f.write(source_file_name)
                if not tarfile.is_tarfile(source_file_name):
                    print('Error reading source: unzipped data is not a tarball')
                    os.rmdir('tmp')
                    return None
        with tarfile.open(source_file_name) as tar:
            tar.extractall(path='tmp')
        files = os.listdir('tmp')
        latex_data = ''
        for file in files:
            if '.tex' in file:
                latex_data += open_file('tmp/' + file) + '\n'
        if latex_data is None:
            os.rmdir('tmp')
            print('Error reading source: tarball does not contain a .tex file')
            return None
        latex_path = 'latex/' + paper_id + '.tex'
        if not os.path.exists(latex_path):
            if not os.path.exists('latex'):
                os.mkdir('latex')
            with open(latex_path, 'w', encoding='utf-8') as f:
                f.write(latex_data)
        sections = read_latex_data(latex_data)
    finally:
        shutil.rmtree('tmp')
    return sections