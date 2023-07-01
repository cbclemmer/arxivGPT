import sys
import json

from arxiv import ArxivGPT

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
    max_tokens = config['max_tokens']

ArxivGPT(config["openai_key"]).read_paper(paper_id, max_tokens)