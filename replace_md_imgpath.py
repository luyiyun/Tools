""" 将md文件中插入的图片的路径进行修改 """
import re
from argparse import ArgumentParser


def replace_md_imgpath(ori_md, target_md, new_image_root, depth):
    pattern = re.compile(r"\!\[(.*?)\]\((.*?)\)")
    fr = open(ori_md, "r")
    fw = open(target_md, "w")

    for line in fr.readlines():
        matchobj = pattern.search(line)
        if matchobj:
            ori_path = matchobj.group(2)
            remain_part = "/".join(ori_path.split("/")[depth:])
            new_path = new_image_root.rstrip("/\\") + "/" + remain_part
            # line = re.replace()
            line = pattern.sub("![\\g<1>](%s)" % new_path, line)
        fw.write(line)

    fr.close()
    fw.close()


def main():
    parser = ArgumentParser()
    parser.add_argument("fn")
    parser.add_argument("image_root")
    parser.add_argument("-d", "--depth", default=-2, type=int)
    args = parser.parse_args()

    assert args.fn.endswith(".md")

    replace_md_imgpath(
        args.fn,
        args.fn[:-3]+"-new.md",
        args.image_root,
        args.depth
    )


if __name__ == "__main__":
    main()