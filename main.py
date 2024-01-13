import os
import sys
import re
import time
import click
import requests
import json
from openai import AzureOpenAI
from jinja2 import Template
from prompts import (
    SYSTEM_PROMPT_FOR_DESIRE, 
    USER_DESIRE_TPL, 
    SYSTEM_PROMPT_FOR_TXT, 
    USER_PROMPT_TPL, 
    SYSTEM_PROMPT_FOR_HTML, 
    SYSTEM_PROMPT_FOR_COVERPAGE_HTML
)

@click.group(invoke_without_command=True)
@click.option(
    "--task",
    "-T",
    help="明确的任务，如：为3岁小男孩编写一本关于太空的绘本",
)
@click.option(
    "--desire",
    "-D",
    help="一个愿望，由模型自动生成多个明确的任务，如：为3岁小男孩编写10本不同主题的绘本",
)
@click.pass_context

def main(
    ctx: click.Context,
    task: str,
    desire: str,
) -> None:
    if ctx.invoked_subcommand is None:
        # 创建 azure openai 客户端
        openai_client = AzureOpenAI(
            azure_endpoint = os.getenv('azure_api_base'),
            api_key = os.getenv('azure_api_key'),
            api_version = os.getenv('azure_api_version')
        )

        # 生成任务列表
        tasks = []
        if task:
            tasks.append(task)
        elif desire:
            completion = openai_client.chat.completions.create(
                model = os.getenv('gpt_deployment_name'),
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_FOR_DESIRE},
                    {"role": "user", "content": Template(USER_DESIRE_TPL).render(user_desire=desire)}
                ]
            )
            output = json.loads(completion.model_dump_json())['choices'][0]['message']['content']
            tasks = re.findall(r"(?<=)-\s*(.*)", output)
        else:
            print('[*] 选项 --task 和 --desire 需至少设置一个')
            sys.exit()

        num = 1
        for task in tasks:
            print(f'[+] 正在生成第{num}本绘本...\n')

            # 调 GPT4 模型接口生成绘本内容
            completion = openai_client.chat.completions.create(
                model = os.getenv('gpt_deployment_name'),
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_FOR_TXT},
                    {"role": "user", "content": Template(USER_PROMPT_TPL).render(user_task=task)}
                ]
            )
            output = json.loads(completion.model_dump_json())['choices'][0]['message']['content']

            print(f'[+] 完成内容生成\n==========\n{output}\n')

            # 解析绘本内容
            title = re.search(r"标题\s*：\s*(.*)", output, re.IGNORECASE).group(1)
            contents = re.findall(r"(?<=\n)-\s*(.*)", output)
            contents.insert(0, title)

            # 调 DALL·E 3 模型接口生成绘本图片
            print(f'[+] 正在生成图片...\n==========\n')
            pb = []
            i = 1
            for content in contents:
                response = openai_client.images.generate(
                    model = os.getenv('dalle_deployment_name'),
                    prompt = f'【卡通风格】{content}' if i == 1 else f'【卡通风格】{title}{content}',
                    n=1
                )
                image_url = json.loads(response.model_dump_json())['data'][0]['url']

                print(f'[{i}] 文本内容：{content} 图片地址：{image_url}\n')

                pb.append({
                    'txt': content,
                    'image_url': image_url
                })

                i += 1

                time.sleep(0.1)

            print(f'[+] 完成图片生成\n\n')

            # 创建绘本输出目录
            outputdir = os.path.join(os.path.dirname(sys.argv[0]), 'output', title)
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)
            
            # 生成包含内容和图片的 HTML 代码
            print(f'[+] 正在生成绘本...\n==========\n')
            i = 1
            for page in pb:
                fn = str(i).zfill(2)
                # 下载图片
                r = requests.get(page.get('image_url'), stream=True)
                if r.status_code == 200:
                    with open(os.path.join(outputdir, f'{fn}.png'), 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)

                # 保存文本内容
                with open(os.path.join(outputdir, f'{fn}.txt'), 'w') as f:
                    f.write(page.get('txt'))

                # 调 GPT4 模型接口生成 HTML 代码
                completion = openai_client.chat.completions.create(
                    model = os.getenv('gpt_deployment_name'),
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT_FOR_COVERPAGE_HTML if i == 1 else SYSTEM_PROMPT_FOR_HTML},
                        {"role": "user", "content": f'文本：{page.get("txt")}，图片地址：{fn}.png'}
                    ]
                )
                html_code = json.loads(completion.model_dump_json())['choices'][0]['message']['content']

                # 将 HTML 代码写入文件
                with open(os.path.join(outputdir, f'{fn}.html'), 'w') as f:
                    f.write(html_code)

                print(f'生成 HTML 文件：{outputdir}/{fn}.html')

                i += 1

                time.sleep(0.1)
            
            print(f'[+] 完成第{num}本绘本：{title}\n')
            num += 1

        print(f'[+] 完成全部绘本生成\n\n')

if __name__ == "__main__":
    main()
