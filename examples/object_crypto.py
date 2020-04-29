# -*- coding: utf-8 -*-

import os
import sys
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey

sys.path.append("/Users/fengyu/aliyun-oss-python-sdk")

import oss2
from oss2 import AliKMSProvider, RsaProvider
from oss2 import models

# 以下代码展示了客户端文件加密上传下载的用法，如下载文件、上传文件等。


# 首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
# 通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。
#
# 以杭州区域为例，Endpoint可以是：
#   http://oss-cn-hangzhou.aliyuncs.com
#   https://oss-cn-hangzhou.aliyuncs.com
# 分别以HTTP、HTTPS协议访问。
access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '')
access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '')
bucket_name = os.getenv('OSS_TEST_BUCKET', '')
endpoint = os.getenv('OSS_TEST_ENDPOINT', '')
cmk = os.getenv('OSS_TEST_CMK', '')
region = os.getenv('OSS_TEST_REGION', '')

# 确认上面的参数都填写正确了
for param in (access_key_id, access_key_secret, bucket_name, endpoint, cmk, region):
    assert '<' not in param, '请设置参数：' + param

key = 'example.txt'
content = b'a' * 1024 * 1024
filename = 'example_file.txt'

private_key = '''-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQCokfiAVXXf5ImFzKDw+XO/UByW6mse2QsIgz3ZwBtMNu59fR5z
ttSx+8fB7vR4CN3bTztrP9A6bjoN0FFnhlQ3vNJC5MFO1PByrE/MNd5AAfSVba93
I6sx8NSk5MzUCA4NJzAUqYOEWGtGBcom6kEF6MmR1EKib1Id8hpooY5xaQIDAQAB
AoGAOPUZgkNeEMinrw31U3b2JS5sepG6oDG2CKpPu8OtdZMaAkzEfVTJiVoJpP2Y
nPZiADhFW3e0ZAnak9BPsSsySRaSNmR465cG9tbqpXFKh9Rp/sCPo4Jq2n65yood
JBrnGr6/xhYvNa14sQ6xjjfSgRNBSXD1XXNF4kALwgZyCAECQQDV7t4bTx9FbEs5
36nAxPsPM6aACXaOkv6d9LXI7A0J8Zf42FeBV6RK0q7QG5iNNd1WJHSXIITUizVF
6aX5NnvFAkEAybeXNOwUvYtkgxF4s28s6gn11c5HZw4/a8vZm2tXXK/QfTQrJVXp
VwxmSr0FAajWAlcYN/fGkX1pWA041CKFVQJAG08ozzekeEpAuByTIOaEXgZr5MBQ
gBbHpgZNBl8Lsw9CJSQI15wGfv6yDiLXsH8FyC9TKs+d5Tv4Cvquk0efOQJAd9OC
lCKFs48hdyaiz9yEDsc57PdrvRFepVdj/gpGzD14mVerJbOiOF6aSV19ot27u4on
Td/3aifYs0CveHzFPQJAWb4LCDwqLctfzziG7/S7Z74gyq5qZF4FUElOAZkz718E
yZvADwuz/4aK0od0lX9c4Jp7Mo5vQ4TvdoBnPuGoyw==
-----END RSA PRIVATE KEY-----'''

public_key = '''-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBAKiR+IBVdd/kiYXMoPD5c79QHJbqax7ZCwiDPdnAG0w27n19HnO21LH7
x8Hu9HgI3dtPO2s/0DpuOg3QUWeGVDe80kLkwU7U8HKsT8w13kAB9JVtr3cjqzHw
1KTkzNQIDg0nMBSpg4RYa0YFyibqQQXoyZHUQqJvUh3yGmihjnFpAgMBAAE=
-----END RSA PUBLIC KEY-----'''

# 初始化阿里云kms方式加密的bucket(推荐)
bucket = oss2.CryptoBucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name,
                           crypto_provider=AliKMSProvider(access_key_id, access_key_secret, region, cmk))

# 初始化RSA方式加密的bucket(不推荐)
# key_pair = {'private_key': private_key, 'public_key': public_key}
# bucket = oss2.CryptoBucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name,crypto_provider = RsaProvider(key_pair))

"""
文件上传
"""
result = bucket.put_object(key, content, headers={'content-length': str(1024 * 1024)})
assert result.status == 200

"""
文件下载
"""

# 下载文件
# 原文件
result = bucket.get_object(key)

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk

assert content_got == content

# 下载原文件到本地文件
result = bucket.get_object_to_file(key, filename)

# 验证一下
with open(filename, 'rb') as fileobj:
    assert fileobj.read() == content

os.remove(filename)

# 下载部分文件
result = bucket.get_object(key, byte_range=(0, 1024))

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got == content[0:1025]

"""
分片上传
"""
part_a = b'a' * 1024 * 100
part_b = b'b' * 1024 * 100
part_c = b'c' * 1024 * 100
multi_content = [part_a, part_b, part_c]

parts = []
data_size = 100 * 1024 * 3
part_size = 100 * 1024
multi_key = "multipart_example.txt"

context = models.MultipartUploadCryptoContext(data_size, part_size)
res = bucket.init_multipart_upload(multi_key, upload_context=context)
upload_id = res.upload_id

# 分片上传
for i in range(3):
    result = bucket.upload_part(multi_key, upload_id, i + 1, multi_content[i], upload_context=context)
    parts.append(oss2.models.PartInfo(i + 1, result.etag, size=part_size, part_crc=result.crc))

# 完成上传
result = bucket.complete_multipart_upload(multi_key, upload_id, parts)

# 下载全部文件
result = bucket.get_object(multi_key)

# 验证一下
content_got = b''
for chunk in result:
    content_got += chunk
assert content_got[0:102400] == part_a
assert content_got[102400:204800] == part_b
assert content_got[204800:307200] == part_c

"""
断点上传
"""
resumable_key = 'resumable.txt'
content = b'a' * 1024 * 1024 * 100
file_name_upload = 'upload.txt'
file_name_download = 'download.txt'

# 将content的内容写入文件
with open(file_name_upload, 'wb') as fileobj:
    fileobj.write(content)

# 这里例子为了演示方便将multipart_threshold的值设置成了100*1024，实际使用用户可以根据使用场景设置，默认值为10MB。
# multipart_threshold表示文件超过这个阈值就是用分片上传方式上传问题，如果文件大小小于这个值就使用简单的put_object接口上传文件
# part_size为使用分片上传时分片的大小,默认值为10MB.
# num_threads为并发上传线程的个数，默认值为1
oss2.resumable_upload(bucket, resumable_key, file_name_upload, multipart_threshold=10 * 1024 * 1024,
                      part_size=1024 * 1024, num_threads=3)

# 断点续传下载
oss2.resumable_download(bucket, resumable_key, file_name_download, multiget_threshold=10 * 1024 * 1024, part_size=1024 * 1024,
                        num_threads=3)

# 验证一下
with open(file_name_download, 'rb') as fileobj:
    assert fileobj.read() == content
