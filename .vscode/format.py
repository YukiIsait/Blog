import sys
import re


def replace_image_syntax(markdown_text: str):
    '''
    将 Markdown 图片片段替换为 Hugo 图片片段
    '''
    return re.sub(r'!\[(.*?)\]\((.*?)\)', r'{{< image src="\2" caption="\1" >}}', markdown_text)


def format_markdown_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    content = replace_image_syntax(content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


if __name__ == '__main__':
    format_markdown_file(sys.argv[1])
