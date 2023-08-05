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
from latex import latex_to_json

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
    return (text, len(pdfReader.pages))

def get_sections(paper_id: str):
    url = f'https://arxiv.org/e-print/{paper_id}'
    response = requests.get(url)
    if response.status_code == 404:
        print(f'Error reading source: recieved 404 for {url}')
        return None
    if response.status_code != 200:
        raise Exception(f'Error downloading source code for paper {paper_id}\n{response.content.decode()}')
    os.path.mkdir('tmp')
    tmp_file_name = 'tmp/paper_source'
    with open(tmp_file_name, 'wb') as f:
        f.write(response.content)
    tar_file = None
    if not tarfile.is_tarfile(tmp_file_name)
        with gzip.open(tmp_file_name) as f:
            gzip_file = f.read()
            tar_file = gzip.decompress(gzip_file)
            os.remove(tmp_file_name)
            with open(tmp_file_name, 'wb') as f:
                f.write(tmp_file_name)
            if not tarfile.is_tarfile(tmp_file_name):
                print('Error reading source: unzipped data is not a tarball')
                os.rmdir('tmp')
                return None
    with tar.open(tmp_file_name) as tar:
        tar.extractall(path='tmp')
    files = os.listdir('tmp')
    latex_file = None
    for file in files:
        if '.tex' in file:
            latex_file = file
    if latex_file is None:
        os.rmdir('tmp')
        print('Error reading source: tarball does not contain a .tex file')
        return None
    sections = latex_to_json('tmp/' + latex_file)
    os.rmdir('tmp')
    return sections