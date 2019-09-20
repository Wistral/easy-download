#!/usr/bin/env python3
#coding=utf8
_description = """一个快速轻量的Python多线程下载脚本
支持多线程下载, 断点续传, MD5自动校验等功能"""

import requests
import pickle
from requests.utils import quote
from pprint import pprint
import subprocess
import os
import progressbar
import numpy as np
import threading
import threading
import time
import argparse
import sys


class DownloadThread(threading.Thread):
    """多线程下载类"""
    terminated = False
    def __init__(self, url, session=None, method='GET', params=None, headers=None, 
                 _from='', to='', size=0, chunk_size=0, *args, **kwargs):
        """可以选择请求类型，URL参数，headers，资源段下载，块大小"""
        threading.Thread. __init__(self)
        self.ss = requests.Session() if session is None else session
        self.url = url
        self.size = 0
        
        if headers:
            self.h = headers.copy()
        else:
            self.h = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/77.0.3865.75 Chrome/77.0.3865.75 Safari/537.36'}
        if isinstance(_from, str) and _from == '':
            self.full_size = size
        else:
            self.h['Range'] = f'Bytes={_from}-{to}'
            self.full_size = to - _from + 1
        self.method = method
        self.chunk_size = chunk_size
        self.chunks = []

    def run(self):
        if self.terminated:
            return
        if self.method == 'GET':
            # 如果设置分块读写
            if self.chunk_size > 0:
                self.response = self.ss.get(self.url, headers=self.h, stream=True)
                code = self.response.status_code
                if code == 206:
                    pass
#                     print('文件分块下载请求成功')
                elif code == 200:
                    if self.h.get('Range', '') != '':
                        print('文件分块下载请求失败,终止')
                elif code == 403:
                    print('下载请求错误', code)
                    print('您的账号可能没有权限或已被限速')
                    self.terminated = True
                    raise "download not authorized"
                elif code == 404:
                    print('找不到资源')
                else:
                    print('unknown', code)
                    print(self.response.text)
                self.size = self.full_size
#                for chunk in self.response.iter_content(chunk_size=self.chunk_size):
#                    self.chunks.append(chunk)
#                    self.size += self.chunk_size
#                print('文件块', self.h['Range'].split('=')[-1], '下载成功')
            else:
                self.response = self.ss.get(self.url, headers=self.h)
                
        elif selff.method == 'POST':
            self.response = self.ss.post(self.url, headers=self.h)
        else:
            print('unknown request method!')


class MultiThread:
    """自动进行多线程下载类"""
    block = 0
    def __init__(self, url, session=None, fn='', md5='', 
    size=0, thread_num=0, verbose=False, *args, **kwargs):
        self.url = url
        self.ss = requests.Session() if session is None else session
        self.n = thread_num
        self.finished = False
        self.v = verbose
        if fn:
            self.fn = fn
        else:
            self.fn = url.split('/')[-1]
            
        print('准备下载文件', self.fn)
        if md5:
            print('将在文件下载完成后进行MD5校验')
        if size:
            self.size = size
        self.get_size()
        
        if not hasattr(self, 'size'):
            print('无法获取文件大小或位置')
            return
        self.download()
        if md5:
            self.check_sum(md5)
            # TODO: 其他方式的文件完整性检查

    def get_size(self):
        # 获取资源的大小，单位字节
        # 当前仅支持1次跳转
        head = self.ss.head(self.url)
        if head.status_code // 100 == 3:
            head = self.ss.head(head.headers['Location'])
        if head.status_code == 200:
            self.size = int(head.headers['Content-Length'])
            return True
        return False

    def check_alive(self):
        if self.finished:
            return
        total = self.pool.keys()
        alive = [k for k, v in self.pool.items() if v.is_alive()]
        if len(alive) < self.n:
            for i in range(self.n - len(alive)):
                c = self.block
                if c <= self.max_block:
                    L, R = self.bp[c-1], self.bp[c]-1
                    t = DownloadThread(self.url, chunk_size=100*1024,
                                        _from=L, to=R)
                    self.pool[c] = t
                    t.start()
                    self.block += 1
                    if self.block == self.max_block:
                        self.finished = True
                
    def check_write(self):
        keys = self.pool.keys()
        sorted(keys)
        to_del = []
        for k in keys:
            thread = self.pool[k]
            if thread.terminated:
                sys.exit(1)
            # 写入序号最小的block，否则等待
            if thread.is_alive():
                break
            else:
                self.file.write(thread.response.content)
                self.file.flush()
                if self.v:
                    print(f'写入block {k}/{self.max_block} {thread.h["Range"][6:]}')
                self.downloaded_size += thread.size
                to_del.append(k)
        # 清除写入过的文件块以回收内存
        for k in to_del:
            self.pool.pop(k)
    
    def check_sum(self, md5):
        print('正在校验MD5...')
        proc = subprocess.Popen(['md5sum', self.fn], stdout=subprocess.PIPE)
        proc.wait()
        if md5 == proc.stdout.read().decode().split('  ')[0]:
            print('文件MD5一致性检测通过')
        else:
            print('[WARN]您的文件的MD5与给定的不一致！')
    
    def download(self, begin=0):
        if self.n == 1:
            t = DownloadThread(self.url, chunk_size=100*1024, size=self.size)
            t.start()
            bar = progressbar.ProgressBar(maxval=self.size, 
                          widgets=[f'[{self.fn[:4]}...]',
                                   progressbar.Percentage(), ' ',
                                  progressbar.Bar(), ' (', 
                                   progressbar.FileTransferSpeed(), '|',
                                   progressbar.Timer(),
                                  '|', progressbar.ETA(),')' ])
            bar.start()
            i = 0
            # 设置分块写入的块大小
            chunk_size = 1024 *512
            chunk_list = []
            with open(self.fn, 'wb') as fn:
                for chunk in t.response.iter_content(chunk_size=chunk_size):
                    if i+chunk_size < self.size:
                        i += chunk_size
                    else:
                        # 确保进度条不会越界报错
                        i = self.size
                    # 分块写入
                    # TODO: 将块数据存储在内存中，最后统一写入，减少写的次数
                    chunk_list.append(chunk)
                    bar.update(i)
                for c in chunk_list:
                    fn.write(c)
            return
        thread_pool = {}
        self.pool = thread_pool
        begin = 0
        chunk_size = 2 * 1024 ** 2
        tmp_fn = self.fn + '.tmp'
        if self.fn in os.listdir('.'):
            print('文件似乎已经下载过了')
            return
        elif tmp_fn in os.listdir('.'):
            begin = os.stat(tmp_fn).st_size
            if begin < self.size:
                print('继续未完成的下载...')
                print('已经下载的大小', begin-1)
        else:
            print('开始新的下载')
        self.max_block = (self.size - begin) // chunk_size
        print('设置最大block', self.max_block)
        breakpoints = [begin + i * chunk_size for i in range(self.max_block+1)]
        breakpoints.append(self.size)
        breakpoints[-1] += 1
        self.bp = breakpoints
        self.block = 1
        print(f'开始多线程下载,线程数{self.n}')
        self.check_alive()
        # 添加进度条（文件名、百分比、进度、下载速度、用时、剩余时间
        # TODO: 文件传输速度在续传的时候显示异常，progressbar不支持的特性
        bar = progressbar.ProgressBar(max_value=self.size,
                                    widgets=[f'[{self.fn[:4]}...{self.fn[-4:]}]',
                                    progressbar.Percentage(), ' ',
                                    progressbar.Bar(), ' (',
                                    progressbar.AdaptiveTransferSpeed(), '|',
                                    progressbar.Timer(),
                                    '|', progressbar.ETA(),')'])
        self.check_alive()
        time.sleep(1)
        bar.start()
        self.file = open(tmp_fn, 'ab+')
        self.downloaded_size = begin
        while self.block < self.max_block or \
        any([t.is_alive() for k, t in self.pool.items()]):
            try:
                time.sleep(.5)
                self.check_alive()
                self.check_write()
                if self.downloaded_size >= self.size:
                    self.downloaded_size = self.size
                bar.update(self.downloaded_size)
            except KeyboardInterrupt:
                print('\n\n下载被终止...')
                self.file.close()
                sys.exit(1)
            except Exception as e:
                print('\n\n其他异常\n')
                self.file.close()
                sys.exit(1)
        self.file.close()
        os.rename(self.fn+'.tmp', self.fn)
        print(f'\n\n文件{self.fn}下载成功')


def _main():
    kwargs = {
        'url': 'http://mirrors.yun-idc.com/ubuntu-releases/18.04.3/ubuntu-18.04.3-live-server-amd64.iso',
        'fn': '',
        'thread_num': 2,
        'md5': '',
        'verbose': False
    }
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--demo', help='下载演示', action="store_true")
    parser.description = _description
    parser.add_argument('url', help='资源URL', type=str, default='')
    parser.add_argument('-n', '--fname', help='下载文件名', type=str)
    parser.add_argument('-t', '--thread-num', help='下载线程数', type=int, default=2)
    parser.add_argument('--md5', help='开启md5校验', type=str)
    parser.add_argument('-v', '--verbose', help='繁琐输出', action="store_true")
    args = parser.parse_args()

    if args.demo:
        kwargs['fn'] = 'ubuntu-18.04.3-live-server-amd64.iso'
        kwargs['thread_num'] = 8
        kwargs['md5'] = 'c038a031a2b638f8e89d897119f1b7bb'
        print('下载器演示，开始下载...')
        print(f'./Downloader.py {kwargs["url"]} -n {kwargs["fn"]} -t {kwargs["thread_num"]} --md5 {kwargs["md5"]}')
    else:
        if args.url:
            kwargs['url'] = args.url
        if args.fname:
            kwargs['fn'] = args.fname
        if args.thread_num:
            kwargs['thread_num'] = args.thread_num
        if args.md5:
            kwargs['md5'] = args.md5
        if args.verbose:
            kwargs['verbose'] = True
    
    try:
        MultiThread(**kwargs)
    except Exception as e:
        print(e)
        return 1
    return 0
    
if __name__ == '__main__':
    sys.exit(_main())
