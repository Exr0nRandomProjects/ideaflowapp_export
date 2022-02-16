from tqdm import tqdm

import requests # to get image from the web
import shutil # to save it locally

import json
from os import path, mkdir
from datetime import datetime

FILENAME = "../../Downloads/personal-2022-2-15.if"

# OUTPUT_DIR = f"{path.basename(FILENAME)}export-{datetime.now()}"
# OUTPUT_DIR = f"{path.basename(FILENAME)}export"
OUTPUT_DIR = f"/Users/albhuan/a1oh/ideaflow"
# mkdir(OUTPUT_DIR) # TODO: add back

class ImageDownloadQueue:
    def __init__(self, output_dir: str):
        try:
            mkdir(output_dir)
        except:
            pass
        self.output_dir = output_dir
        self.download_queue = []
    def __len__(self):
        return len(self.download_queue)
    def push(self, url, filename):
        self.download_queue.append((url, filename))
    def download(self):
        url, filename = self.download_queue.pop(0)
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(f"{self.output_dir}/{filename}", 'wb') as wf:
                shutil.copyfileobj(r.raw, wf)
            yield (True, filename)
        else:
            yield (False, filename)


def convert(flow, rich_content=False, frontmater_ignore=[]):
    def generate_frontmatter(dict, ignore_keys=['tokens', 'asText'] + frontmater_ignore, filter_none=True):
        fm = { k: v for k, v in dict.items() if k not in ignore_keys and (filter_none and v is not None) }
        return "---\n" + '\n'.join(f'{k}: {v}' for k, v in fm.items()) + "\n---\n"

    def serialize_tok(tok, img_downloader):
        ret = ''
        print(tok)
        match tok['type']:
            case 'paragraph' | 'list' | 'listItem':
                for child in tok['content']:
                    ret += serialize_tok(child, img_downloader)
                ret += '\n'
            case 'codeblock':
                ret += '```'
                for child in tok['content']:
                    ret += serialize_tok(child, img_downloader)
                ret += '\n```\n'
            case 'spaceship':
                if tok['linkedNoteId'] is not None:
                    ret += '[' + tok['linkedNoteId'] + ']'
            case 'text':
                ret += tok['content']
            case 'hashtag':
                ret += tok['content'].replace('*', '/')
            case 'image':
                fname = path.basename(tok['src'])
                img_downloader(tok['src'], fname)
                size_text = "" if tok['width'] is None else f" ={tok['width']}x"
                ret += f"![(image)](./{fname}{size_text})"
            case 'checkbox':
                ret += f"[{'x' if tok['isChecked'] else ' '}]"
            case 'link':
                ret += f"[{tok['slug']}]({tok['content']})"
            case _:
                raise NotImplementedError(f"node type {tok['type']} is not implemented")

        # if 'children' in note:
        #     for child in note['children']:
        #         ret += serialize_note(child)
        return ret

    downloader = ImageDownloadQueue(OUTPUT_DIR)

    notes = flow['notes']
    print(f"found {len(notes.keys())} notes...")
    for id, note in tqdm(notes.items()):
        if id != 'atM8UbNuFh': continue
        if rich_content == True:
            # raise NotImplementedError("TODO: implement recursive traversal to extract rich content")
            output = ''.join(serialize_tok(tok, img_downloader=downloader.push) for tok in note['tokens'])
        else:
            output = note['asText']

        print(note['asText'])

        with open(f"{OUTPUT_DIR}/{id}.md", 'w') as wf:
            wf.write(generate_frontmatter(note) + note['asText'])

    print(f"downloading {len(downloader)} images...")
    for res, fname in tqdm(downloader.download()):
        if not res: print(f"downloading {fname} failed!")

if __name__ == '__main__':
    with open(FILENAME, 'r') as rf:
        flow = json.loads(rf.read())

    if flow['version'] == 16:
        # convert(flow, frontmater_ignore=['position', 'authorId', 'readAll', 'insertedAt'])
        convert(flow, rich_content=True)
    else:
        raise NotImplementedError(f"not implemented for ideaflow version {flow['version']}")
