# -*- coding=utf-8

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys, argparse
import logging




logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='## %Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)


secret_id =  # 替换为用户的secret_id
secret_key =   # 替换为用户的secret_key
region = 'ap-beijing'  # 替换为用户的region
token = None  # 使用临时密钥需要传入Token，默认为空,可不填
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
client = CosS3Client(config)




"""
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
"""

transition = ["STANDARD_IA", "ARCHIVE", "DEEP_ARCHIVE"]


def check_lifecycle(cos_name):
    try:
        response = client.get_bucket_lifecycle(Bucket=cos_name)
        # print(response)
        return response
    except Exception as erro:
        return None


def not_owned_add_lifecycle(cos_patch, cos_storage_class, storage_class_day):
    try:
        num = 1
        template = {'Rule': [{'ID': str(num),
                              'Filter': {'Prefix': cos_patch},
                              'Status': 'Enabled'}]}
        if cos_storage_class in transition:
            transition_class = {'Transition': [{'Days': storage_class_day, 'StorageClass': cos_storage_class}]}
            template['Rule'][0].update(transition_class)
            return template
        elif cos_storage_class == "Expiration":
            delete_patch_file = {'Expiration': {'Days': storage_class_day}}
            template['Rule'][0].update(delete_patch_file)
            logging.info(template)
            return template
    except Exception as erro:
        logging.error(erro)


def owned_add_lifecycle(cos_patch, cos_storage_class, storage_class_day, template):
    try:
        if template['Rule'][-1]['ID'].isdigit():
            num = int(template['Rule'][-1]['ID']) + 1
            update_class = {'ID': str(num),
                            'Filter': {'Prefix': cos_patch},
                            'Status': 'Enabled'}
            if cos_storage_class in transition:
                transition_class = {'Transition': [{'Days': storage_class_day, 'StorageClass': cos_storage_class}]}
                update_class.update(transition_class)
                template['Rule'].append(update_class)
                return template
            elif cos_storage_class == "Expiration":
                delete_patch_file = {'Expiration': {'Days': storage_class_day}}
                update_class.update(delete_patch_file)
                template['Rule'].append(update_class)
                # print(delete_patch_file)
                return template
        else:
            for i in template['Rule'][::-1]:
                if i['ID'].isdigit():
                    num = int(i['ID']) + 1
                    update_class = {'ID': str(num),
                                    'Filter': {'Prefix': cos_patch},
                                    'Status': 'Enabled'}
                    if cos_storage_class in transition:
                        transition_class = {'Transition': [{'Days': storage_class_day, 'StorageClass': cos_storage_class}]}
                        update_class.update(transition_class)
                        template['Rule'].append(update_class)
                        return template
                    elif cos_storage_class == "Expiration":
                        delete_patch_file = {'Expiration': {'Days': storage_class_day}}
                        update_class.update(delete_patch_file)
                        template['Rule'].append(update_class)
                        return template
            else:
                logging.info("已经配置过生命周期，但是没有按照数字！")
                num = 1
                update_class = {'ID': str(num),
                                'Filter': {'Prefix': cos_patch},
                                'Status': 'Enabled'}
                if cos_storage_class in transition:
                    transition_class = {'Transition': [{'Days': storage_class_day, 'StorageClass': cos_storage_class}]}
                    update_class.update(transition_class)
                    template['Rule'].append(update_class)
                    return template
                elif cos_storage_class == "Expiration":
                    delete_patch_file = {'Expiration': {'Days': storage_class_day}}
                    update_class.update(delete_patch_file)
                    template['Rule'].append(update_class)
                    return template
    except Exception as erro:
        logging.error(erro)


def update_lifecycle(cos_name, template):
    try:
        client.put_bucket_lifecycle(Bucket=cos_name, LifecycleConfiguration=template)
        logging.info("Cos桶：{}中已添加：".format(cos_name) + str(template['Rule'][-1]) + "这条规则")
    except Exception as erro:
        logging.error(erro)


def main(cos_name, cos_patch, cos_storage_class, storage_class_day):
    """
    :param cos_name 桶的名称
    :param cos_patch 指的是Cos路径
    :param cos_storage_class 指的是存储类型：类型包括  低频 归档 深度归档和删除
    :param storage_class_day 指定的天数
    :param template 现有规则
    """
    if check_lifecycle(cos_name):
        if len(check_lifecycle(cos_name)['Rule']) <= 1000:
            template = owned_add_lifecycle(cos_patch, cos_storage_class, storage_class_day, check_lifecycle(cos_name))
            if template == "nonum":
                if not check_lifecycle(cos_name):
                    template = not_owned_add_lifecycle(cos_patch, cos_storage_class, storage_class_day)
                else:
                    template = check_lifecycle(cos_name)
            update_lifecycle(cos_name, template)
            logging.info("默认夜间00:00开始执行！请耐心等待")
        else:
            logging.error("当前规则已大于1000条，无法继续添加，请先联系运维清理原规则！")
            sys.exit(1)
    else:
        template = not_owned_add_lifecycle(cos_patch, cos_storage_class, storage_class_day)
        update_lifecycle(cos_name, template)



def command_line_arguments_parse():
    argument_parser = argparse.ArgumentParser(description='Tencent Cloud Cos Lifecycle Management Tool')
    argument_parser.add_argument(
        '--cos_name', '-b', type=str, help='Cos bucket name .', dest='cos_name', default=None
    )
    argument_parser.add_argument(
        '--storage_class_day', '-d', type=str, help='The number of days in the cos rule，60 days by default',
        dest='storage_class_day',
        default=60
    )
    argument_parser.add_argument(
        '--cos_storage_class', '-c', type=str, help='Cos storage type ["STANDARD_IA低频存储", "ARCHIVE归档存储存储", '
                                                    '"DEEP_ARCHIVE深度归档存储", '
                                                    '"Expiration删除"]', dest='cos_storage_class', default=None
    )
    argument_parser.add_argument(
        '--cos_patch', '-p', type=str, help='Fill in the Cos path, please use "," to separate multiple paths.',
        dest='cos_patch', default=None
    )
    return argument_parser.parse_args()


if __name__ == "__main__":
    args = command_line_arguments_parse()
    if all([args.cos_name, args.cos_storage_class, args.cos_patch]):
        for cos_patch in args.cos_patch.split(','):
            main(args.cos_name, cos_patch, args.cos_storage_class, args.storage_class_day)
    else:
        logging.error("没有填写必填参数,桶名称：{}，桶类型：{}，桶路径：{}".format(args.cos_name, args.cos_storage_class, args.cos_patch))


