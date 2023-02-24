import sys
import os
import subprocess
import requests

def transcribe(path_to_file):
    # The output is another file named path_to_file.txt
    path_to_txt_file = f"{path_to_file}.txt"

    if not os.path.exists(path_to_txt_file):
        print('Transcribing audio file using whisper...')
        # Run the whisper shell command to transcribe the audio file from python code
        # whisper path_to_file -f txt --verbose False
        subprocess.run(["whisper", path_to_file, "-f", "txt", "--verbose", "False"])

    # Copy the contents of the file to a variable and delete the file
    text = ""
    with open(path_to_txt_file, "r") as f:
        text = f.read()

    def cleanup():
        os.remove(path_to_txt_file)

    return text, cleanup

def get_openai_token():
    '''
    Read openai token from ~/.openai config file and return it
    if it's not present then prompt the user to add token to the said
    file
    '''
    config_file = os.path.expanduser("~/.openai")
    if not os.path.exists(config_file):
        print('Please add your openai api token to the ~/.openai file')
        sys.exit(1)
    
    token = None
    with open(config_file, "r") as f:
        token = f.read().strip()
    return token

def cleanup_using_openai_api(text):
    '''
    curl https://api.openai.com/v1/completions \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer YOUR_API_KEY' \
    -d '{
    "model": "text-davinci-003",
    "prompt": "Say this is a test",
    "max_tokens": 7,
    "temperature": 0
    }'

    '''
    print('Cleaning up text using openai api...')

    prompt_template = """
    Clean up the following text and format if for markdown, remove filler words and add punctuation.
    Split into paragraphs where necessary, make sure to use double line breaks.

    {text}

    The output should be the formatted text with no whitespace before or after.
    """
    api_token = get_openai_token()
    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={"Authorization": f"Bearer {api_token}"},
        json={
            "model": "text-davinci-003",
            "prompt": prompt_template.format(text=text),
            "max_tokens": text.count(" ") * 2,
            "temperature": 0.2,
        }
    ).json()
    return response["choices"][0]["text"].strip()

def generate_title_using_openai_api(text):
    '''
    curl https://api.openai.com/v1/completions \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer YOUR_API_KEY' \
    -d '{
    "model": "text-davinci-003",
    "prompt": "Say this is a test",
    "max_tokens": 7,
    "temperature": 0
    }'

    '''
    print('Generating a title using openai api...')

    prompt_template = """
    Generate a suitable title for the following text. The title should be short and concise.

    {text}

    The output should be the title with no whitespace or quotes.
    """
    api_token = get_openai_token()
    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={"Authorization": f"Bearer {api_token}"},
        json={
            "model": "text-davinci-003",
            "prompt": prompt_template.format(text=text),
            "max_tokens": text.count(" ") * 2,
            "temperature": 0.4,
        }
    ).json()
    return response["choices"][0]["text"].strip().strip('"')


def format_md(text, title, source):
    template = """
# {title}

{text}

## Source

![[{source}]]

    """
    return template.format(title=title, text=text, source=source).lstrip()

def write_to_md(text, title):
    # Write the text to the markdown file
    with open(f"{title}.md", "w") as f:
        f.write(text)

def rename_file(path_to_audio, title):
    # Rename the audio file to the title of the text
    # but keep the original extension
    extension = path_to_audio.split(".")[-1]
    new_path = f"{title}.{extension}"
    os.rename(path_to_audio, new_path)
    return new_path

def main():
    # Get command line argument as path to audio file
    path_to_audio = sys.argv[1]
    text, cleanup = transcribe(path_to_audio)

    text = cleanup_using_openai_api(text)
    title = generate_title_using_openai_api(text)
    
    path_to_audio = rename_file(path_to_audio, title)

    text = format_md(text, title, path_to_audio)
    write_to_md(text, title)
    
    cleanup()
