
'StorageClass':设置存储类型
STANDARD_IA: 低频存储
ARCHIVE:  归档存储存储
DEEP_ARCHIVE：深度归档存储
'Expiration': {'Days': '360'} 表示删除文件并指定天数
"""
"""
:param cos_name 桶的名称
:param cos_patch 指的是Cos路径
:param cos_storage_class 指的是存储类型：类型包括  低频 归档 深度归档和删除
:param storage_class_day 指定的天数
:param template 现有规则

支持的路径生命周期规则是1W条，多余这个条数将无法添加


填写SecretID  KEY 在主文件里面

其余可以直接python3 Cos_TTL.py --传参  可以传的参数 

:param cos_name 桶的名称

:param cos_patch 指的是Cos路径

:param cos_storage_class 指的是存储类型：类型包括  低频 归档 深度归档和删除

:param storage_class_day 指定的天数

