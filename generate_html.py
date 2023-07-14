import json
from util import open_file, save_file

def generate_html(title: str, completions_file: str) -> str:
  # conversation indexes
  new_summary_idx = 6

  html = f'<h1>{title}</h1>'
  file_data = open_file(completions_file)
  html_template = open_file('html_template.html')
  conversations = [json.loads(conv) if len(conv) > 0 else [] for conv in file_data.split('\n')]
  words = 0
  for conversation in conversations:
    if len(conversation) < 1:
      continue
    
    new_summary = conversation[new_summary_idx]['content'].replace('Summary:\n\n', '')
    words += len(new_summary.split(' '))
    html += '<div class=\'summary\'>'
    for line in new_summary.split('\n'):
      html += f'<p>{line}</p>\n'
    html += '</div>'

  return f'<p>Words: {words}, Chunks: {len(conversations)}</p>' + html_template.replace('<!-- TEXT -->', html).replace('<!-- TITLE -->', 'TEST')