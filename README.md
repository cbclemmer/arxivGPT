### ArxivGPT
  
This is a bot that uses open AI's Chat GPT3.5 (the chat model, not the davinci model) api to read a research paper from arxiv.  
  
### Setup
Install libraries: `pip install -r requirements.txt`  
Create `config.json` in root directory it should look something like this:
```
{
  "openai_key": "[API_KEY]",
  "max_tokens": "30000"
}
```
**Options:**  
**openai_key:** api key from open ai (org key is not needed)  
**max_tokens:** (Optional, default: 30,000) maximum number of tokens to read. Paper will be trunkated and everything will work normally if paper is over the limit  
  
### Usage
Each paper at arxiv.org uses a unique id to identify it, you can find this id in the url  
**example:** (id: 2303.08774) https://arxiv.org/abs/2303.08774  

Run the program using this id like:  
`python main.py [ARXIV ID]`  
  
It will first get the preview page and extract the abstract:  
```
> python3 main.py 2005.14165
Title: [2005.14165] Language Models are Few-Shot Learners

Abstract:  Recent work has demonstrated substantial gains on many NLP tasks and
benchmarks by pre-training on a large corpus of text followed by fine-tuning on
a specific task. While typically task-agnostic in architecture, this method
still requires task-specific fine-tuning datasets of thousands or tens of
thousands of examples. By contrast, humans can generally perform a new language
task from only a few examples or from simple instructions - something which
current NLP systems still largely struggle to do. Here we show that scaling up
language models greatly improves task-agnostic, few-shot performance, sometimes
even reaching competitiveness with prior state-of-the-art fine-tuning
approaches. Specifically, we train GPT-3, an autoregressive language model with
175 billion parameters, 10x more than any previous non-sparse language model,
and test its performance in the few-shot setting. For all tasks, GPT-3 is
applied without any gradient updates or fine-tuning, with tasks and few-shot
demonstrations specified purely via text interaction with the model. GPT-3
achieves strong performance on many NLP datasets, including translation,
question-answering, and cloze tasks, as well as several tasks that require
on-the-fly reasoning or domain adaptation, such as unscrambling words, using a
novel word in a sentence, or performing 3-digit arithmetic. At the same time,
we also identify some datasets where GPT-3's few-shot learning still struggles,
as well as some datasets where GPT-3 faces methodological issues related to
training on large web corpora. Finally, we find that GPT-3 can generate samples
of news articles which human evaluators have difficulty distinguishing from
articles written by humans. We discuss broader societal impacts of this finding
and of GPT-3 in general.

    
Read paper?: Yes
```  

You can then add a note that the bot should keep in mind while reading the paper and it will try to address it in its summary:  
```
What should I keep in mind while reading the paper? (leave blank if no notes)
Notes: How does the size of a language model affect its performance?
```  
  
The paper will then be read into the chat gpt3.5 api 2500 tokens at a time and the bot will return a summary of the text with a maximum of 500 tokens.
Once 4 chunks of text has been summarized, another bot will summarize the summaries. That summary will be prepended to the list of summaries for the next overall summarization.
This process will repeat until the paper is finished or the maximum token count is reached. The last overall summary will be used as the final output.

### Output Folders
**logs/**  
All output written to the screen is saved to this folder. It is the most verbose and probably the least useful.  
  
**completions/**  
Every prompt and completion given to gpt3 is saved in this folder. Useful for training your own bot (depends on a 4k+ context length).  
  
**summaries/**  
The final overall summary of the paper. This is the summarization of the paper, and it should also contain useful information about your notes you gave the bot.

**papers/**  
The pdf downloaded to analyze, saved as `papers/[paper_id].pdf`