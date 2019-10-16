#! /bin/env python3

import os
import time
import re
from re import Pattern, Match

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
POST_PATH = os.path.join(BASE_PATH, 'posts')

post_template = ''
readme_template = ''
filename_format = r'{num:03d}-{title}.md'
filename_patt = r'^(\d+)\-([\S\s]+)\.md$'


def load_template():
    global post_template
    global readme_template

    with open(os.path.join(BASE_PATH, 'templates', 'post_template.md'), 'r', encoding='utf-8') as f:
        post_template = f.read()
    
    with open(os.path.join(BASE_PATH, 'templates', 'readme_template.md'), 'r', encoding='utf-8') as f:
        readme_template = f.read()
    


def get_files_name(path):
    sub_nodes = os.listdir(path)
    files = list(
        filter(
            lambda n: os.path.isfile(os.path.join(path, n)),
            sub_nodes
        )
    )
    return files


def get_next_number(files: list):
    nums = []
    patt: Pattern = re.compile(filename_patt)
    for f in files:
        m = patt.match(f)
        if not m:
            continue
        nums.append(int(m.group(1)))
    if not nums:
        return 0
    else:
        return max(nums) + 1


def new_post(title: str, num=None):
    if num is None:
        num = get_next_number(get_files_name(POST_PATH))
    filename = filename_format.format(num=num, title=title)
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    with open(os.path.join(POST_PATH, filename), 'w', encoding='utf-8') as f:
        f.write(post_template.format(date=date, title=title))


def make_readme():
    header = '| No | Title | Date |\n| --- | --- | --- |\n'
    a_post = '| {number} | [{title}]({file}) | {date} |'
    files = get_files_name(POST_PATH)
    post_tuples = []

    title_patt = re.compile(r'^\s*title\s*:\s*([\S]*\S)\s?$', re.M)
    date_patt = re.compile(r'^\s*date\s*:\s*([\d\-]+\s*[\d:]+)\s?$', re.M)
    file_patt = re.compile(filename_patt)

    for filename in files:
        first_or_empty = lambda l, group=0: l[group] if l else ''

        title = ''
        date = ''
        number = first_or_empty(file_patt.match(filename), 1)

        with open(os.path.join(POST_PATH, filename), 'r', encoding='utf-8') as file:
            text = file.read()
            title = first_or_empty(title_patt.findall(text))
            date = first_or_empty(date_patt.findall(text))

        post_tuples.append((number, title or 'untitled', os.path.join('.', 'posts', filename), date))
    
    post_tuples.sort(key=lambda t: t[0])
    toc = header + '\n'.join(
        map(
            lambda t: a_post.format(number=t[0], title=t[1], file=t[2], date=t[3]),
            post_tuples
        )
    )
    
    with open('README.md', 'w', encoding='utf-8') as file:
        file.write(readme_template.format(toc=toc))


def main(args: list):
    load_template()
    if args[0].lower() == 'new':
        if len(args) < 2:
            print('Need title.')
            os.sys.exit(2)
        title = args[1]
        num = None
        if len(args) >= 3 and re.match(r'^\d+$', args[2]):
            num = int(args[2])
        new_post(title, num)
        print(f'Create successfully: {title}')
    elif args[0].lower() == 'readme':
        make_readme()
        print('Make README.md Successfully.')
    else:
        print('No command named {}'.format(args[0]))


if __name__ == "__main__":
    argv = os.sys.argv
    if len(argv) < 2:
        print('Need more argv.')
        os.sys.exit(1)
    main(argv[1:])
