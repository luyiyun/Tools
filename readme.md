# 自用小工具

## 将`ipynb`文件转换为`md`文件

有时候我会使用`ipynb`来进行学习和记录笔记，为了能够将其与其他markdown笔记整合，需要将其转换为markdown格式。jupyter自带的转换太过死板，得到的格式也比较难看，所以自己写了一个小程序，用来做这个事情。

使用方式：

```bash
ipynb2md.exe fn.ipynb
```

选项:

* `fn.ipynb`: 要转换的`ipynb`文件
* `-t`: 目标文件名，默认为当前文件名（后缀改为`.md`，即`fn.md`）
* `--image_path`: 保存图片的文件夹，默认为目标文件名（即`fn/`）

## 更改`md`文件中图片链接的路径

如果将markdown文件转移到其他位置，则其中的图片路径也需要进行改变，此程序用来执行这个任务。为了保险起见，此程序将会复制一个新的文件`fn-new.md`，在其上进行更改。

```bash
replace_md_imagepath.exe fn.md ../images
```

选项:

* `fn.md`: 要进行更改的`md`文件
* `--images_root`: 新的图片路径前缀
* `--depth`: 保留的图片路径的部分，默认是`-2`。比如原始的图片路径为`./X/Y/img.png`，`images_root`为`../imgs`，若`depth=-2`，则保留的部分为`Y/img.png`，得到的新路径为`../imgs/Y/img.png`