from tqdm import tqdm

import json
from os import path, mkdir
from datetime import datetime

FILENAME = "../../Downloads/personal-2022-2-15.if"

# OUTPUT_DIR = f"{path.basename(FILENAME)}export-{datetime.now()}"
OUTPUT_DIR = f"{path.basename(FILENAME)}export"
mkdir(OUTPUT_DIR)

def convert(flow, create_links=False, frontmater_ignore=[]):
    def generate_frontmatter(dict, ignore_keys=['tokens', 'asText'] + frontmater_ignore, filter_none=True):
        fm = { k: v for k, v in dict.items() if k not in ignore_keys and (filter_none and v is not None) }
        return "---\n" + '\n'.join(f'{k}: {v}' for k, v in fm.items()) + "\n---"

    notes = flow['notes']
    print(f"found {len(notes.keys())} notes...")
    for id, note in tqdm(notes.items()):
        if create_links == True:
            raise NotImplementedError("TODO: implement recursive traversal to extract rich content")
        else:
            with open(f"{OUTPUT_DIR}/{id}.md", 'w') as wf:
                wf.write(generate_frontmatter(note) + note['asText'])

if __name__ == '__main__':
    with open(FILENAME, 'r') as rf:
        flow = json.loads(rf.read())

    if flow['version'] == 16:
        # convert(flow, frontmater_ignore=['position', 'authorId', 'readAll', 'insertedAt'])
        convert(flow)
    else:
        raise NotImplementedError(f"not implemented for ideaflow version {flow['version']}")
