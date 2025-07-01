import env
from utils import time
from time import sleep
from pathlib import Path
from requests import Session
from json import dump, load, loads
from html2text import html2text

DATA = Path(__file__).parent / 'data'
DATA.mkdir(exist_ok=True)

session = Session()
session.verify = False  # Disable SSL verification for simplicity
session.headers.update({
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
})
session.cookies.update({
    "userId": env.userId,
    "serviceToken": env.serviceToken,
})

entries_list = []


def get_entries(syncTag: str = ''):
    url = f"https://i.mi.com/note/full/page?ts={time()}&limit=200"
    if syncTag:
        url += f"&syncTag={syncTag}"
    r = session.get(url)
    data = r.json()['data']
    entries_list.extend(data['entries'])
    print(
        f"Fetched {len(data['entries'])} entries, total: {len(entries_list)}")
    if data['lastPage'] == False:
        sleep(1)
        get_entries(data['syncTag'])


def parse_entry(entry: dict):
    extraInfo = loads(entry.get('extraInfo', '{}'))
    return {
        "id": entry['id'],
        "title": extraInfo.get('title'),
        "type": entry['type'],
        "createDate": entry['createDate'],
        "modifyDate": entry['modifyDate'],
    }


def content2markdown(content: str):
    content = content.replace('<bullet indent="1" />', '<li />')
    return html2text(content)


def get_entry(id: str, title, replace: bool = False):
    print(f"Fetching entry {id} - {title}")
    url = f"https://i.mi.com/note/note/{id}/?ts={time()}"
    dir_name = id
    if title:
        dir_name += '-' + title.replace('/', '-').replace('\\', '-')
    dir = DATA / dir_name
    try:
        dir.mkdir(exist_ok=True)
    except:
        dir = DATA / id
        dir.mkdir(exist_ok=True)
    if not replace and (dir / 'data.json').exists():
        print(f"Entry {id} already exists, skipping.")
        return
    r = session.get(url)
    data = r.json()['data']['entry']
    with open(dir / 'data.json', 'w', encoding='utf-8') as f:
        dump(data, f, ensure_ascii=False, indent=4)
    if 'setting' not in data:
        data['setting'] = {}
    if 'data' not in data['setting']:
        data['setting']['data'] = []
    for i in data['setting']['data']:
        fileId = i['fileId']
        file = session.get(
            f"https://i.mi.com/file/full?type=note_img&fileid={fileId}")
        with open(dir / f"{fileId}.jpg", 'wb') as f:
            f.write(file.content)
    print(f"Fetched entry and {len(data['setting']['data'])} images.")


if __name__ == "__main__":
    # print("Fetching entries...")
    # get_entries()
    # entries_file = DATA / 'entries.json'
    # with open(entries_file, 'w', encoding='utf-8') as f:
    #     dump(entries_list, f, ensure_ascii=False, indent=4)
    # print(f"Entries saved to {entries_file}")
    with open(DATA / 'entries.json', 'r', encoding='utf-8') as f:
        entries_list = load(f)
    print(f"Loaded {len(entries_list)} entries from file.")
    for _entry in entries_list:
        entry = parse_entry(_entry)
        get_entry(entry["id"], entry['title'])
        sleep(1)
