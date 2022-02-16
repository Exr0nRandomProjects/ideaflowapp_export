FILENAME = "../../Downloads/personal-2022-2-15.if"
OUTPUT_DIR = f"{path.basename(FILENAME)}export"




from tqdm import tqdm

import requests # to get image from the web
import shutil # to save it locally

import json
from os import path, mkdir
from datetime import datetime

mkdir(OUTPUT_DIR)

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
        while len(self.download_queue):
            url, filename = self.download_queue.pop(0)
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                r.raw.decode_content = True
                with open(f"{self.output_dir}/{filename}", 'wb') as wf:
                    shutil.copyfileobj(r.raw, wf)
                yield (True, filename)
            else:
                yield (False, filename)


def convert(flow, rich_content=True, frontmater_ignore=[]):
    def generate_frontmatter(dict, ignore_keys=['tokens', 'asText'] + frontmater_ignore, filter_none=True):
        fm = { k: v for k, v in dict.items() if k not in ignore_keys and (filter_none and v is not None) }
        return "---\n" + '\n'.join(f'{k}: {v}' for k, v in fm.items()) + "\n---\n"

    def serialize_tok(tok, img_downloader, depth=-1):
        ret = []
        match tok['type']:
            case 'listItem':
                ret.append('\t'*(int(tok['depth']) if tok['depth'] is not None else 0) + '- ' + ''.join(
                        ''.join(serialize_tok(child, img_downloader, depth=depth+1))
                        for child in tok['content']
                    ))
            case 'paragraph' | 'list':
                ret.append(''.join(
                        ''.join(serialize_tok(child, img_downloader, depth=depth))
                        for child in tok['content']
                    ) + '\n')
            case 'codeblock':
                ret.append('```' +
                    '\n'.join(
                        ''.join(serialize_tok(child, img_downloader, depth=depth))
                        for child in tok['content'])
                + '\n```\n')
            case 'spaceship':
                if tok['linkedNoteId'] is not None:
                    # ret.append('[[ife_' + tok['linkedNoteId'] + ']]') # use wikilinks
                    try:
                        link_slug = flow['notes'][tok['linkedNoteId']]['asText'].split('\n')[0]
                    except KeyError:
                        link_slug = "(unknown note '{tok['linkedNoteId']}')"
                    ret.append(f"[{link_slug}](ife_{tok['linkedNoteId']}) ")
            case 'text':
                ret.append(tok['content'])
            case 'hashtag':
                ret.append(tok['content'].replace('*', '/'))
            case 'image':
                fname = path.basename(tok['src'])
                img_downloader(tok['src'], fname)
                size_text = "" if tok['width'] is None else f" ={tok['width']}x"
                ret.append(f"![(image)](./{fname}{size_text})")
            case 'checkbox':
                ret.append("[{'x' if tok['isChecked'] else ' '}]")
            case 'link':
                ret.append(f"[{tok['slug']}]({tok['content']})")
            case _:
                raise NotImplementedError(f"node type {tok['type']} is not implemented")

        return ['    ' * max(depth, 0) + x for x in ret]

    downloader = ImageDownloadQueue(OUTPUT_DIR)

    notes = flow['notes']
    print(f"found {len(notes.keys())} notes...")
    for id, note in tqdm(notes.items()):
        if rich_content == True:
            output = ''.join(''.join(serialize_tok(tok, img_downloader=downloader.push)) for tok in note['tokens'])
        else:
            output = note['asText']

        # print(json.dumps(note['tokens'], indent=4))
        # print(note['asText'])
        # print(output)

        with open(f"{OUTPUT_DIR}/ife_{id}.md", 'w') as wf:
            wf.write(generate_frontmatter(note) + output)

    print(f"downloading {len(downloader)} images...")
    for res, fname in tqdm(downloader.download(), total=len(downloader)):
        if not res: print(f"downloading {fname} failed!")

if __name__ == '__main__':
    with open(FILENAME, 'r') as rf:
        flow = json.loads(rf.read())

    if flow['version'] == 16:
        convert(flow, frontmater_ignore=['position', 'authorId', 'readAll', 'insertedAt'])
    else:
        raise NotImplementedError(f"not implemented for ideaflow version {flow['version']}")
