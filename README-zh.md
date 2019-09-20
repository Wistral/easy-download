## simple pydownload

一个由纯python完成的简易下载器

### 目前支持的特性

- [x] 下载文件
- [x] 断点续传(分段下载)
- [x] 多线程下载
- [x] MD5自动校验
- [x] 进度条显示(进度, 速度, 剩余时间...)


### 依赖
```sh
pip3 install progressbar2 requests --user
```

### 下载示例
以下载[ubuntu-18.04.3-live-server-amd64.iso](http://mirrors.yun-idc.com/ubuntu-releases/18.04.3/ubuntu-18.04.3-live-server-amd64.iso)为例

- 普通下载
    ```sh
    python3 Downloader.py http://mirrors.yun-idc.com/ubuntu-releases/18.04.3/ubuntu-18.04.3-live-server-amd64.iso
    ```

- 校验MD5
    ```sh
    python3 Downloader.py http://mirrors.yun-idc.com/ubuntu-releases/18.04.3/ubuntu-18.04.3-live-server-amd64.iso --md5 c038a031a2b638f8e89d897119f1b7bb
    ```
- 8线程下载并在下载完成后校验MD5
    ```sh
    python3 Downloader.py http://mirrors.yun-idc.com/ubuntu-releases/18.04.3/ubuntu-18.04.3-live-server-amd64.iso -t 8 --md5 c038a031a2b638f8e89d897119f1b7bb
    ```
    >准备下载文件 ubuntu-18.04.3-live-server-amd64.iso<br>
    将在文件下载完成后进行MD5校验<br>
    开始新的下载<br>
    设置最大block 424<br>
    开始多线程下载,线程数8<br>
    [ubun....iso] 28% |##      | (  9.0 MiB/s|Elapsed Time: 0:00:31|ETA:   0:01:20)

命令的详细介绍
```sh
python3 Downloader.py -h
```

### 未来可能实现的功能或要解决的问题
- 下载会有小概率MD5不一致的情况(文件损坏)

    原因暂不明, 若提示MD5不一致建议重新下载
- 进度条在续传后显示异常大
- 携带状态信息下载