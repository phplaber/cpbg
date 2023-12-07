# cpbg
Children's picture book generator - 儿童绘本生成器

## 简介

**cpbg** 就是用来生成儿童绘本的工具。你只需输入一段文本提示，可以是具体的任务（如：为3岁小男孩编写一本关于太空的绘本）或者是愿望（如：为3岁小男孩编写10本不同主题的绘本），接下来就可以离开位置去冲一杯美味的咖啡，剩下的工作交给程序去做。顺便说一句，背后真正干活的是 AI。

## 用法

运行工具，需安装 Python 3.6+。同时依赖 Azure OpenAI 服务，所以需先在 Azure 平台上部署模型。部署完成后，设置如下环境变量：

```bash
$ export azure_api_base="https://xxxx.openai.azure.com/" // 终结点
$ export azure_api_key="xxxx"                            // 密钥
$ export gpt_deployment_name="xxxx"                      // GPT 4 模型部署名称
$ export dalle_deployment_name="xxxx"                    // DALL-E 3 模型部署名称
```

下载项目后，切换到项目目录。使用 pip3 安装依赖包：

```bash
$ pip3 install -r requirements.txt
```

简单查看下帮助文档

```bash
$ python3 main.py --help
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  -T, --task TEXT    明确的任务，如：为3岁小男孩编写一本关于太空的绘本
  -D, --desire TEXT  一个愿望，由模型自动生成多个明确的任务，如：为3岁小男孩编写10本不同主题的绘本
  --help             Show this message and exit.
```

就是这样，赶快试试吧。

## 原理

首先，如果用户输入的是期望，则先通过该期望，结合系统提示，让 GPT 4 模型生成多个具体的任务。

其次，遍历这些任务。通过任务，结合系统提示，让 GPT 4 模型生成以任务为主题的内容，包括标题和段落。接着，依次以标题和段落为提示文本，让 DALL-E 3 模型生成相关图片。将图片下载到本地后，结合文字、图片和系统提示，让 GPT 4模型将文字和图片结合，生成一个个 HTML 网页，即绘本页。

这样，就生成了一本绘声绘色的绘本了。

如果对系统提示有兴趣，可查看脚本 **prompts.py**。

## 示例

![第一关](/demo/04.png "第一关")
![第三关](/demo/06.png "第三关")
