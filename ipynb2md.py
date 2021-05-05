"""
ipynb文件格式解析(https://nbformat.readthedocs.io/en/latest/format_description.html)：
ipynb是一个json文件，所以其内容就是嵌套的键值对。
{
    metadata(dict):                       // 关于使用的语言和kernel的信息
    {
        kernel_info:
        language_info:
    }
    nbformat(int):                        // 格式的版本，以下格式只适用于4版本
    nbformat_minor(int):
    cells(list):
    [
        {                                 // Markdown Cell
            cell_type(str): markdown,
            metadata(dict): {},
            source(str or list):
            attachments(dict): {
                test.png: {image/png: base64-data},
                ...
            }
        },
        {                                 // Raw Cell
            cell_type(str): raw,
            metadata(dict): {},
            source(str or list):
            attachments(dict): {
                test.png: {image/png: base64-data},
                ...
            }
        },
        {                                 // Code Cell
            cell_type(str): code,
            metadata(dict): {},           // 记录各种元数据，给插件用，比如运行时间，是否折叠等等
            source(str or list):
            execution_count(int or null): // 运行编号
            outputs(list):
            [
                {                         // 使用print或!cat等输出的信息
                    output_type(str): stream,
                    name(str): stdout (or stderr),
                    text(list of str): [],
                },
                {                         // 富文本信息，也包括图像
                    output_type(str): display_data,
                    metadata(dict):       // 输出的元信息，比如图像的大小
                    {
                        image/png(dict): {width(int): , height(int): },
                        ...
                    }
                    data(dict):
                    {
                        text/plain(list of str): [],
                        image/png(list of base64-data): [],
                        application/json(dict): ???,
                        application/vnd.exampleorg.type+json(dict): ???
                    }
                },
                {                          // 代码运行结果，与display_data基本一致
                    output_type(str): execute_result,
                    execution_cout(int): ,
                    metadata(dict):
                    {
                        image/png(dict): {width(int): , height(int): },
                        ...
                    }
                    data(dict):
                    {
                        text/plain(list of str): [],
                        image/png(list of base64-data): [],
                        application/json(dict): ???,
                    }
                },
                {                           // 运行失败的结果
                    output_type(str): error,
                    ename(str):,
                    evalue(str):,

                    traceback(list):[],
                },
                ...
            ]
        },
        ...
    ]
}
"""


import os
import json
import base64
from argparse import ArgumentParser


MD_LIST_PREFIX = ("* ", "- ")
OUTPUT_PREFIX = "#> "
img_id = 0


def save_png(data, fn):
    with open(fn, 'wb') as f:
        f.write(base64.b64decode(data.strip()))


def write_stream_line(writer, line):
    for ll in line.split("\n"):
        writer.write("%s%s\n" % (OUTPUT_PREFIX, ll))


def parse_md_raw_cell(writer, cell, img_path):
    global img_id
    for line in cell["source"]:
        if line.endswith("  \n"):
            # 在jupyter markdown中，想要进行单行换行，必须使用`  \n`，而在typora中则
            # 直接使用`\n`即可
            line = line[:-3] + "\n"
        writer.write(line)
        # cell的最后一行，只有一行的cell，其后面都没有`\n`，需要添加一个。
        writer.write("\n")

    if "attachments" in cell:
        for k, v in cell["attachments"]:
            if "image/png" in v:
                fn = img_path + ("/image_%d.png" % img_id)
                save_png(v["image/png"], fn)
            writer.write("\n![%s](%s)\n" % (k, fn))
            img_id += 1


def parse_code_cell(writer, cell, img_path):
    global img_id
    # 整理运行编号
    #  当没有运行编号（比如没有运行）时，使用`-`代替
    if cell["execution_count"] is None:
        exec_count = "-"
    else:
        exec_count = str(cell["execution_count"])
    # 代码块开头
    writer.write("```python\n")
    writer.write("# In [%s]:\n" % exec_count)
    # 源代码部分
    writer.writelines(cell["source"])
    writer.write("\n")
    # 如果输出不为空，则再加一个换行符，让代码和输出分割比较明显
    if cell["outputs"]:
        writer.write("\n")

    # 用于保存图片
    images = []
    # 整理输出
    for output in cell["outputs"]:
        # 使用`print`或`!cat`等的输出，其output_type为stream，name是stdout
        if output["output_type"] == "stream":
            if output["name"] == "stdout":
                for line in output["text"]:
                    # steam的输出有可能将多行以一个字符串的形式保存
                    # 这时候需要特殊处理，才能让每一行前面都有#>
                    write_stream_line(writer, line)
            else:
                print(output["name"])
                raise NotImplementedError
        # 直接运行代码或使用plt.show()的结果
        elif output["output_type"] in ["display_data", "execute_result"]:
            output_data = output["data"]
            if "text/plain" in output_data:
                for line in output_data["text/plain"]:
                    writer.write(OUTPUT_PREFIX + line)
                writer.write("\n")
            if "image/png" in output_data:
                if isinstance(output_data["image/png"], str):
                    output_imgs = [output_data["image/png"]]
                elif isinstance(output_data["image/png"], list):
                    output_imgs = output_data["image/png"]
                else:
                    print(type(output_data["image/png"]))
                    raise NotImplementedError
                for i, imgdata in enumerate(output_imgs):
                    fn = img_path + ("/image_%d.png" % img_id)
                    save_png(imgdata, fn)
                    images.append(fn)
                    img_id += 1
        # 运行失败的结果
        elif output["output_type"] == "error":
            writer.write("%s !ERROR %s:%s\n" %
                         (OUTPUT_PREFIX, output["ename"], output["evalue"]))
        else:
            print("output_type == %s" % output["output_type"])
            raise NotImplementedError

    # 代码块结尾
    writer.write("```")
    # 将图片写上
    if images:
        for img in images:
            writer.write("\n![](%s)\n" % img)

    # TODO: metadata记录各种元数据，一般是插件的数据，比如看执行时间
    # TODO: 图片大小


def ipynb2markdown(ipynb_fn, md_fn, img_path):
    # img_path = img_root.rstrip("/\\") + "/" + os.path.basename(ipynb_fn)[:-6]
    os.makedirs(img_path, exist_ok=True)
    # 读取内容
    with open(ipynb_fn, "r") as f:
        content = json.load(f)
    # 以上处理方式只适用于版本为4.0之后的ipynb文件
    assert content["nbformat"] == 4
    # TODO: 将python版本、虚拟环境等信息加入其中
    # 将内容进行处理，写入markdown文件
    with open(md_fn, "w") as writer:
        for i, cell in enumerate(content["cells"]):
            if cell["cell_type"] == "markdown":
                parse_md_raw_cell(writer, cell, img_path)
            elif cell["cell_type"] == "code":
                parse_code_cell(writer, cell, img_path)
            else:
                print("cell_type == %s" % cell["cell_type"])
                raise NotImplementedError
            # 每个cell之间使用两个换行符来进行间隔
            writer.write("\n\n")


def main():
    parser = ArgumentParser()
    parser.add_argument("fn")
    parser.add_argument(
        "-t", "--to", default=None,
        help="The target filename, default is fn.md"
    )
    parser.add_argument(
        "--image_path", default=None,
        help="The path contain images"
    )
    args = parser.parse_args()

    if args.to is None:
        args.to = args.fn[:-6] + ".md"
    if args.image_path is None:
        args.image_path = args.to[:-3]

    assert args.fn.endswith(".ipynb")
    assert args.to.endswith(".md")

    ipynb2markdown(args.fn, args.to, args.image_path)


if __name__ == "__main__":
    main()
