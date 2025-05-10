import asyncio
import logging
import json
import os
import datetime

import requests
import re
from config import get_config
from model import QuickLinksData, YuqueBook, YuqueDocs, YuqueDocDetail, YuqueGroup
import os

logger = logging.getLogger(__name__)


def sanitize_filename(title: str) -> str:
    """
    将语雀文档标题转换为合法的文件名

    :param title: 文档标题
    :return: 合法的文件名
    """
    # 替换Windows和Unix系统中不允许的文件名字符
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    filename = title

    # 替换非法字符为下划线
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # 去除首尾空格
    filename = filename.strip()

    # 如果文件名为空，提供默认名称
    if not filename:
        filename = "untitled_document"

    # 限制文件名长度，避免过长
    if len(filename) > 200:
        filename = filename[:200]

    return filename


class Yuque:
    def __init__(self):
        config = get_config()["yuque"]

        self.base_url = config.get("base_url")

        if self.base_url is None:
            logger.error("未设置语雀 base url")
            return

        # request
        self._token = config.get("token")
        self._session = config.get("session")

        if self._token is None or self._session is None:
            logger.error("未设置语雀 Token 或 session.")
            return

        self._requestSession = requests.session()
        self._requestSession.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        }
        self._requestSession.cookies.update({
            "yuque_ctoken": self._token,
            "_yuque_session": self._session
        })

        if not self._test():
            logger.error("语雀测试未通过")

    def _test(self):
        response = self._requestSession.get(
            self.base_url + "/api/mine/getRecommendationTip?type=activityLive")
        if response.status_code == 200:
            return True
        return False

    async def books(self) -> list[YuqueBook]:
        """
        获取知识库
        :return:  知识库列表
        """
        params = {
            "offset": 0,  # 分页 偏移
            "limit": 100,  # 分页 大小
            "query": "",  # 查询
            "user_type": "Group"  # 固定
        }
        api = "/api/mine/user_books"

        url = self.base_url + api

        response = self._requestSession.get(url, params=params)
        response.raise_for_status()
        return [YuqueBook(g) for g in response.json()["data"]]

    async def docs(self, book: YuqueBook) -> list[YuqueDocs]:
        """
        获取知识库的文档列表
        :return:  文档列表
        """
        params = {
            "book_id": book.id,
        }
        api = "/api/docs"

        url = self.base_url + api

        response = self._requestSession.get(url, params=params)
        response.raise_for_status()
        return [YuqueDocs(g) for g in response.json()["data"]]

    async def docs_export(self, book: YuqueBook, doc: YuqueDocs, save_path: str, retry: int = 1) -> bool:
        """
        导出文档到本地

        :param book:        知识库对象
        :param doc:         文档对象
        :param save_path:   保存路径
        :param retry:       重试次数
        :return:            是否成功
        """
        if retry == 0:
            logger.error(f"导出文档失败，已达到最大重试次数: {book.name} - {doc.title}")
            return False

        data = {
            "force": 0,
            "options": "{\"latexType\":1}",
            "type": "markdown",
        }
        api = f"/api/docs/{doc.id}/export"

        try:
            url = self.base_url + api
            # logger.info(f"正在请求导出文档: {book.name} - {doc.title}")
            response = self._requestSession.post(url, json=data, headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "content-type": "application/json",
                "accept": "application/json",
                "referer": self.base_url,
                "yuque_ctoken": self._token,
                "_yuque_session": self._session
            })

            if response.status_code != 200:
                if (response.json()["message"] == "请发布后再导出"):
                    logger.warning(f"(未发布 跳过下载) {book.name} - {doc.title} ")
                    return False
                if response.status_code == 404:
                    return False

                logger.error(
                    f"导出请求失败，状态码: {response.status_code}，文档: {book.name} - {doc.title}")
                # 请求失败时增加等待时间
                # await asyncio.sleep(5)
                return await self.docs_export(book, doc, save_path, retry=retry-1)

            response.raise_for_status()

            # 解析响应获取下载URL
            response_data = response.json()
            if "data" not in response_data or "url" not in response_data["data"]:
                logger.error(
                    f"导出响应格式错误: {response_data}，文档: {book.name} - {doc.title}")
                # await asyncio.sleep(5)
                return await self.docs_export(book, doc, save_path, retry=retry-1)

            url = response_data["data"]["url"]
            logger.info(f"获取到下载链接，准备下载文档: {book.name} - {doc.title}")

            # 下载文档内容
            download_response = self._requestSession.get(url)

            if download_response.status_code == 200:
                download_response.encoding = download_response.apparent_encoding
                content = download_response.content

                header_content = f"""
```meta_data
知识库名称：{book.name} ({book.id})
介绍：{book.description} 
于{book.created_at}创建，最近更新在{book.updated_at}.
---
文档名称：{doc.title} ({doc.id})
介绍：{doc.description} ({doc.custom_description})
于{doc.created_at}最近更新在{doc.updated_at}.
于{doc.user}创建,最近被{doc.last_editor}编辑.
---
原文地址: {self.base_url}/{book.slug}/{doc.slug} 
"""

                # 协助者信息
                try:
                    doc_detail: YuqueDocDetail = await self.overview(book, doc)
                    header_content += "由"
                    for contributor in doc_detail.contributors:
                        header_content += f"{contributor.name}({contributor.login}) "
                    header_content += "编辑"
                except Exception as e:
                    logger.warning(
                        f"获取文档协助者信息失败: {e}，文档: {book.name} - {doc.title}")

                header_content += "\n```\n\n"

                try:
                    content = re.sub(
                        r'<font\s+style="[^"]*">(.*?)</font>', r'\1', content.decode('utf-8'))

                    # 确保目录存在
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    # 先写入临时文件，成功后再重命名，避免写入失败导致文件损坏
                    temp_path = save_path + ".temp"
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(header_content + content)

                    # 如果文件存在则先备份
                    if os.path.exists(save_path):
                        backup_path = save_path + ".bak"
                        try:
                            if os.path.exists(backup_path):
                                os.remove(backup_path)
                            os.rename(save_path, backup_path)
                        except Exception as e:
                            logger.warning(
                                f"创建备份文件失败: {e}，文档: {book.name} - {doc.title}")

                    # 重命名临时文件为目标文件
                    os.replace(temp_path, save_path)

                    logger.info(
                        f"下载成功: {book.name} - {doc.title} ({save_path})")
                    return True
                except Exception as e:
                    logger.error(f"保存文件时出错: {e}，文档: {book.name} - {doc.title}")
                    return False

            elif download_response.status_code == 422:
                logger.warning(f"文档导出未就绪，等待后重试: {book.name} - {doc.title}")
                # 增加等待时间，避免频繁请求
                # await asyncio.sleep(retry * 2 + 3)
                return await self.docs_export(book, doc, save_path, retry=retry-1)
            else:
                logger.error(
                    f"下载文档失败，状态码: {download_response.status_code}，文档: {book.name} - {doc.title}")
                # await asyncio.sleep(5)
                return await self.docs_export(book, doc, save_path, retry=retry-1)

        except Exception as e:
            logger.exception(f"导出文档过程中发生异常: {e}，文档: {book.name} - {doc.title}")
            # 增加等待时间
            # await asyncio.sleep(retry * 2)
            return await self.docs_export(book, doc, save_path, retry=retry-1)

    async def overview(self, book: YuqueBook, doc: YuqueDocs) -> YuqueDocDetail:
        """
        获取文档详细
        :return:  获取文档详细
        """

        api = f"/api/docs/{doc.slug}?include_contributors=true&include_like=true&include_hits=true&merge_dynamic_data=false&book_id={book.id}"

        url = self.base_url + api

        response = self._requestSession.get(url)
        response.raise_for_status()

        return YuqueDocDetail(response.json()["data"])

    async def quick_links(self) -> QuickLinksData:
        api = f"/api/mine/group_quick_links"
        url = self.base_url + api

        response = self._requestSession.get(url)
        response.raise_for_status()
        return QuickLinksData(response.json()["data"])

    async def groups(self) -> list[YuqueGroup]:
        params = {
            "offset": 0,
            "limit": 200,
        }
        api = f"/api/mine/groups"
        url = self.base_url + api

        response = self._requestSession.get(url, params=params)
        response.raise_for_status()
        return [YuqueGroup(i) for i in response.json()["data"]]


async def download_all():
    """下载所有语雀文档"""
    from config import get_config
    import concurrent.futures

    cfg = get_config()
    yuque = Yuque()

    try:
        # 加载已有的版本信息
        versions = await load_document_versions()

        logger.info("开始下载所有文档...")
        books = await yuque.books()
        logger.info(f"共发现 {len(books)} 个知识库")

        total_docs_count = 0
        success_count = 0
        skip_count = 0
        fail_count = 0

        for book in books:
            try:
                docs = await yuque.docs(book)
                doc_count = len(docs)
                total_docs_count += doc_count

                # 创建导出任务列表
                export_tasks = []

                # 所有 doc
                for doc in docs:
                    if doc.type != "Doc":

                        skip_count += 1
                        continue

                    base_path = os.path.abspath(cfg["save_path"])
                    dir_path = os.path.join(
                        base_path, sanitize_filename(book.name))
                    os.makedirs(dir_path, exist_ok=True)
                    save_path = os.path.join(
                        dir_path, sanitize_filename(doc.title) + ".md")

                    if os.path.exists(save_path):
                        # 检查文件是否需要更新
                        has_update = await check_document_updates(yuque, book, doc, versions)
                        if not has_update:
                            # logger.info(f"文档已存在且无更新: {book.name} - {doc.title}")
                            skip_count += 1
                            continue
                        else:
                            logger.info(
                                f"文档已存在但有更新，将重新下载: {book.name} - {doc.title}")

                    # 添加到任务列表
                    export_tasks.append((doc, save_path))

                # 根据任务数量调整并发数，避免过多并发导致API限制
                max_workers = min(3, len(export_tasks))
                if max_workers == 0:
                    # logger.info(f"知识库 {book.name} 中没有需要下载的文档")
                    continue

                # logger.info(f"开始下载 {book.name} 中的 {len(export_tasks)} 篇文档，并发数: {max_workers}")

                # 使用线程池并发导出文档
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 创建异步任务
                    loop = asyncio.get_event_loop()
                    futures = [
                        loop.run_in_executor(
                            executor,
                            lambda b, d, p: asyncio.run(
                                yuque.docs_export(b, d, p)),
                            book,
                            doc,
                            path
                        )
                        for doc, path in export_tasks
                    ]

                    # 等待所有任务完成
                    results = await asyncio.gather(*futures)

                    # 处理结果
                    for (doc, _), ok in zip(export_tasks, results):
                        if ok:
                            # 更新文档版本信息
                            versions = await update_document_version(versions, book, doc)
                            success_count += 1
                            logger.info(f"下载成功: {book.name} - {doc.title}")
                        else:
                            fail_count += 1
                            # logger.error(f"下载失败: {book.name} - {doc.title}")

                # 每个知识库处理完后保存一次版本信息，避免中途中断导致信息丢失
                await save_document_versions(versions)

                # 知识库之间添加延迟，避免请求过于频繁
                # await asyncio.sleep(2)

            except Exception as e:
                logger.exception(f"处理知识库时出错: {e}，知识库: {book.name}")

        # 最终保存版本信息
        await save_document_versions(versions)

        # 输出统计信息
        logger.info("=" * 40)
        logger.info("下载任务完成！统计信息：")
        logger.info(f"总知识库数: {len(books)}")
        logger.info(f"总文档数:   {total_docs_count}")
        logger.info(f"下载成功:   {success_count} 篇")
        logger.info(f"无需下载:   {skip_count} 篇")
        logger.info(f"下载失败:   {fail_count} 篇")
        logger.info("=" * 40)

    except Exception as e:
        logger.exception(f"下载过程中发生错误: {e}")
        return False

    return True

# 文档版本记录相关函数


def get_version_file_path():
    """获取存储文档版本信息的文件路径"""
    cfg = get_config()
    base_path = os.path.abspath(cfg["save_path"])
    return os.path.join(base_path, "document_versions.json")


async def load_document_versions():
    """加载文档版本信息"""
    version_file = get_version_file_path()
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载文档版本信息失败: {e}")
    return {}


async def save_document_versions(versions):
    """保存文档版本信息"""
    version_file = get_version_file_path()
    try:
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存文档版本信息失败: {e}")
        return False


async def check_document_updates(yuque_client, book: YuqueBook, doc: YuqueDocs, versions: dict):
    """检查文档是否有更新"""
    doc_key = f"{book.id}_{doc.id}"

    # 获取当前版本信息
    current_version = versions.get(doc_key, {})
    current_updated_at = current_version.get("updated_at", "")

    # 如果文档的更新时间比记录的更新时间新，说明有更新
    if doc.updated_at > current_updated_at:
        return True

    return False


async def update_document_version(versions, book: YuqueBook, doc: YuqueDocs):
    """更新文档版本信息"""
    doc_key = f"{book.id}_{doc.id}"
    versions[doc_key] = {
        "book_id": book.id,
        "book_name": book.name,
        "doc_id": doc.id,
        "doc_title": doc.title,
        "updated_at": doc.updated_at,
        "last_check_time": datetime.datetime.now().isoformat()
    }
    return versions


async def monitor_updates():
    """监控文档更新并下载"""
    cfg = get_config()
    yuque = Yuque()

    # 加载已保存的文档版本信息
    versions = await load_document_versions()

    logger.info(f"开始监控语雀文档更新，当前时间: {datetime.datetime.now().isoformat()}")

    try:
        books = await yuque.books()
        update_count = 0
        fail_count = 0

        for book in books:
            try:
                docs = await yuque.docs(book)

                docs.sort(key=lambda d: d.updated_at, reverse=True)

                for doc in docs:
                    if doc.type != "Doc":
                        continue

                    try:
                        has_update = await check_document_updates(yuque, book, doc, versions)

                        if has_update:

                            base_path = os.path.abspath(cfg["save_path"])
                            dir_path = os.path.join(
                                base_path, sanitize_filename(book.name))
                            os.makedirs(dir_path, exist_ok=True)
                            save_path = os.path.join(
                                dir_path, sanitize_filename(doc.title) + ".md")

                            export_success = await yuque.docs_export(book, doc, save_path)

                            if export_success:
                                # 更新版本信息
                                versions = await update_document_version(versions, book, doc)

                    except Exception as e:
                        logger.exception(
                            f"处理文档时出错: {e}，文档: {book.name} - {doc.title}")

            except Exception as e:
                logger.exception(f"获取或处理知识库文档列表时出错: {e}，知识库: {book.name}")

        # 保存更新后的版本信息
        await save_document_versions(versions)
        logger.info(
            f"监控完成，共更新 {update_count} 篇文档，失败 {fail_count} 篇，当前时间: {datetime.datetime.now().isoformat()}")

    except Exception as e:
        logger.exception(f"监控更新过程中发生错误: {e}")


async def download_and_monitor(interval_minutes=60):
    """下载所有文档并持续监控更新"""
    cfg = get_config()

    try:
        # 首次运行时下载所有文档
        logger.info("首次运行，下载所有文档...")
        await download_all()

        # 持续监控更新
        while True:
            try:
                await monitor_updates()
                logger.info(f"等待 {interval_minutes} 分钟后再次检查更新...")
                await asyncio.sleep(interval_minutes * 60)  # 将分钟转换为秒
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                logger.info("等待60秒后重试...")
                # await asyncio.sleep(60)  # 出错后等待1分钟再继续
    except Exception as e:
        logger.exception(f"程序运行过程中发生严重错误: {e}")
        logger.info("程序将退出，请检查错误原因后重新启动。")
