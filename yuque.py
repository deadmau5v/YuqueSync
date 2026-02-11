# -*- coding: utf-8 -*-
import asyncio
import concurrent.futures
import logging
import json
import os
import datetime

import requests
import re
from config import get_config
from model import QuickLinksData, YuqueBook, YuqueDocs, YuqueDocDetail, YuqueGroup

logger = logging.getLogger(__name__)

EXPORT_PENDING_WAIT_SECONDS = 10
MAX_EXPORT_WORKERS = 3


def get_file_extension(export_format: str = None) -> str:
    """
    根据导出格式获取文件扩展名

    :param export_format: 导出格式 ("pdf" 或 "markdown")
    :return: 文件扩展名 (包含点号)
    """
    if export_format is None:
        cfg = get_config()
        export_format = cfg.get("export_format", "pdf")

    return ".pdf" if export_format == "pdf" else ".md"


def sanitize_filename(title: str) -> str:
    """
    将语雀文档标题转换为合法的文件名

    :param title: 文档标题
    :return: 合法的文件名
    """
    # 替换Windows和Unix系统中不允许的文件名字符
    invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    filename = title

    # 替换非法字符为下划线
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # 去除首尾空格
    filename = filename.strip()

    # 如果文件名为空，提供默认名称
    if not filename:
        filename = "untitled_document"

    # 限制文件名长度，避免过长
    if len(filename) > 200:
        filename = filename[:200]

    return filename


def format_book_context(book: YuqueBook) -> str:
    """生成知识库日志上下文。"""
    return f"book={book.name}({book.id})"


def format_doc_context(book: YuqueBook, doc: YuqueDocs) -> str:
    """生成文档日志上下文。"""
    return f"{format_book_context(book)} doc={doc.title}({doc.id})"


def build_doc_save_path(
    base_path: str, book: YuqueBook, doc: YuqueDocs, export_format: str = None
) -> str:
    """构建文档保存路径，并确保目录存在。"""
    book_dir = os.path.join(os.path.abspath(base_path), sanitize_filename(book.name))
    os.makedirs(book_dir, exist_ok=True)
    filename = sanitize_filename(doc.title) + get_file_extension(export_format)
    return os.path.join(book_dir, filename)


def get_export_format() -> str:
    """获取导出格式配置。"""
    cfg = get_config()
    return cfg.get("export_format", "pdf")


def get_export_payload(export_format: str) -> dict:
    """根据导出格式构建导出请求参数。"""
    if export_format == "pdf":
        return {
            "type": "pdf",
            "force": 0,
            "options": '{"enableToc":1}',
        }

    return {
        "force": 0,
        "options": '{"latexType":1}',
        "type": "markdown",
    }


def backup_existing_file(save_path: str, context: str) -> None:
    """如果目标文件已存在，先备份到 .bak。"""
    if not os.path.exists(save_path):
        return

    backup_path = save_path + ".bak"
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(save_path, backup_path)
    except Exception as exc:
        logger.warning(
            "[file] 创建备份失败 %s path=%s error=%s", context, save_path, exc
        )


def save_content_atomically(
    save_path: str, content, binary: bool, context: str
) -> bool:
    """原子化保存文件内容，失败时避免破坏原文件。"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    temp_path = save_path + ".temp"

    try:
        if binary:
            with open(temp_path, "wb") as file_handle:
                file_handle.write(content)
        else:
            with open(temp_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)

        backup_existing_file(save_path, context)
        os.replace(temp_path, save_path)
        return True
    except Exception as exc:
        logger.error("[file] 保存文件失败 %s path=%s error=%s", context, save_path, exc)
        return False


def run_doc_export_sync(
    yuque_client, book: YuqueBook, doc: YuqueDocs, save_path: str
) -> bool:
    """在线程池中执行异步导出逻辑。"""
    return asyncio.run(yuque_client.docs_export(book, doc, save_path))


class Yuque:
    def __init__(self):
        config = get_config()["yuque"]

        self.base_url = config.get("base_url")
        self.is_initialized = False

        if self.base_url is None:
            logger.error("[init] 未设置语雀 base_url")
            return

        # request
        self._token = config.get("token")
        self._session = config.get("session")

        if self._token is None or self._session is None:
            logger.error(
                "[init] 未设置语雀 Token 或 Session，请设置环境变量 YUQUE_TOKEN 和 YUQUE_SESSION"
            )
            return

        if not self._token or not self._session:
            logger.error(
                "[init] 语雀 Token 或 Session 为空，请检查环境变量配置或 .env 文件"
            )
            return

        self._requestSession = requests.session()
        self._requestSession.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json",
        }
        self._requestSession.cookies.update(
            {"yuque_ctoken": self._token, "_yuque_session": self._session}
        )

        if not self._test():
            logger.error("[init] 语雀连接测试失败，请检查 Token 和 Session")
            logger.error(
                "[init] 获取方式: 浏览器登录语雀 → F12 → Network → 请求头 Cookie"
            )
            return

        self.is_initialized = True
        logger.info("[init] 语雀客户端初始化成功")

    def _test(self):
        test_url = self.base_url + "/api/mine/getRecommendationTip?type=activityLive"
        try:
            response = self._requestSession.get(test_url)
            if response.status_code == 200:
                return True

            logger.error("[init] 连接测试失败 status=%s", response.status_code)
            return False
        except Exception as exc:
            logger.error("[init] 连接测试异常 error=%s", exc)
            return False

    def _extract_books_data(self, data):
        if isinstance(data, list):
            return data

        if isinstance(data, dict) and isinstance(data.get("books"), list):
            return data["books"]

        return None

    def _parse_books(self, books_data: list, api_name: str) -> list[YuqueBook]:
        books = []
        for idx, book_item in enumerate(books_data):
            try:
                if isinstance(book_item, dict) and isinstance(
                    book_item.get("target"), dict
                ):
                    book_data = book_item["target"]
                else:
                    book_data = book_item

                books.append(YuqueBook(book_data))
            except Exception as exc:
                logger.warning(
                    "[books] 解析知识库失败 api=%s index=%s error=%s",
                    api_name,
                    idx + 1,
                    exc,
                )

        return books

    def _build_export_headers(self) -> dict:
        return {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "content-type": "application/json",
            "accept": "application/json",
            "referer": self.base_url,
            "yuque_ctoken": self._token,
            "_yuque_session": self._session,
        }

    def _is_unpublished_export(self, response) -> bool:
        try:
            return response.json().get("message") == "请发布后再导出"
        except Exception:
            return False

    async def _build_markdown_header(self, book: YuqueBook, doc: YuqueDocs) -> str:
        context = format_doc_context(book, doc)
        contributors_text = ""

        try:
            doc_detail: YuqueDocDetail = await self.overview(book, doc)
            contributors = [
                f"{contributor.name}({contributor.login})"
                for contributor in doc_detail.contributors
            ]
            if contributors:
                contributors_text = f"由{' '.join(contributors)} 编辑"
        except Exception as exc:
            logger.warning("[export] 获取协作者信息失败 %s error=%s", context, exc)

        lines = [
            "```meta_data",
            f"知识库名称：{book.name} ({book.id})",
            f"介绍：{book.description}",
            f"于{book.created_at}创建，最近更新在{book.updated_at}.",
            "---",
            f"文档名称：{doc.title} ({doc.id})",
            f"介绍：{doc.description} ({doc.custom_description})",
            f"于{doc.created_at}创建，最近更新在{doc.updated_at}.",
            f"于{doc.user}创建，最近被{doc.last_editor}编辑.",
            "---",
            f"原文地址: {self.base_url}/{book.slug}/{doc.slug}",
        ]

        if contributors_text:
            lines.append(contributors_text)

        lines.extend(["```", ""])
        return "\n".join(lines)

    def _save_pdf_export(self, content: bytes, save_path: str, context: str) -> bool:
        return save_content_atomically(save_path, content, binary=True, context=context)

    async def _save_markdown_export(
        self,
        book: YuqueBook,
        doc: YuqueDocs,
        content_text: str,
        save_path: str,
        context: str,
    ) -> bool:
        header_content = await self._build_markdown_header(book, doc)
        markdown_body = re.sub(
            r'<font\s+style="[^"]*">(.*?)</font>', r"\1", content_text
        )
        return save_content_atomically(
            save_path, header_content + markdown_body, binary=False, context=context
        )

    async def books(self) -> list[YuqueBook]:
        """
        获取知识库
        使用通用接口
        /api/mine/user_books

        :return:  知识库列表
        """
        if not self.is_initialized:
            logger.error("[books] 客户端未初始化，无法获取知识库")
            return []

        api_config = {
            "name": "user_books",
            "path": "/api/mine/user_books",
            "params": {
                "offset": 0,
                "limit": 100,
                "query": "",
                "user_type": "User",
            },
        }
        # 非主站就是企业版
        if self.base_url != "https://www.yuque.com":
            api_config["params"]["user_type"] = "Group"

        api_name = api_config["name"]
        api_path = api_config["path"]
        api_params = api_config["params"]
        url = self.base_url + api_path

        logger.info("[books] 请求知识库 api=%s", api_name)
        try:
            response = (
                self._requestSession.get(url, params=api_params)
                if api_params
                else self._requestSession.get(url)
            )

            if response.status_code != 200:
                logger.warning(
                    "[books] 请求失败 api=%s status=%s",
                    api_name,
                    response.status_code,
                )
                response.raise_for_status()

            response_json = response.json()
            if "data" not in response_json:
                logger.warning("[books] 响应缺少 data 字段 api=%s", api_name)
                raise ValueError("响应JSON中缺少 data 字段")

            books_data = self._extract_books_data(response_json["data"])
            if books_data is None:
                logger.warning("[books] 响应数据结构无法识别 api=%s", api_name)
                raise ValueError("无法识别的知识库数据结构")

            if not books_data:
                logger.warning("[books] 知识库列表为空 api=%s", api_name)
                return []

            books = self._parse_books(books_data, api_name)
            logger.info("[books] 获取成功 api=%s count=%s", api_name, len(books))
            return books

        except requests.exceptions.RequestException as exc:
            logger.error("[books] 网络请求异常 api=%s error=%s", api_name, exc)
            raise
        except json.JSONDecodeError as exc:
            logger.error("[books] JSON 解析失败 api=%s error=%s", api_name, exc)
            raise
        except Exception as exc:
            logger.error("[books] 处理异常 api=%s error=%s", api_name, exc)
            raise

    async def docs(self, book: YuqueBook) -> list[YuqueDocs]:
        """
        获取知识库的文档列表
        :return:  文档列表
        """
        if not self.is_initialized:
            logger.error("[docs] 客户端未初始化 %s", format_book_context(book))
            return []

        context = format_book_context(book)
        url = self.base_url + "/api/docs"

        try:
            response = self._requestSession.get(url, params={"book_id": book.id})
            if response.status_code != 200:
                logger.error(
                    "[docs] 获取失败 %s status=%s", context, response.status_code
                )
                response.raise_for_status()

            response_json = response.json()
            docs_data = response_json.get("data")
            if not isinstance(docs_data, list):
                raise ValueError("data 字段不是列表类型")

            docs = []
            for idx, doc_data in enumerate(docs_data):
                try:
                    docs.append(YuqueDocs(doc_data))
                except Exception as exc:
                    logger.warning(
                        "[docs] 解析文档失败 %s index=%s error=%s",
                        context,
                        idx + 1,
                        exc,
                    )

            logger.info("[docs] 获取成功 %s count=%s", context, len(docs))
            return docs
        except Exception as exc:
            logger.error("[docs] 获取文档列表异常 %s error=%s", context, exc)
            raise

    async def docs_export(
        self, book: YuqueBook, doc: YuqueDocs, save_path: str, retry: int = 5
    ) -> bool:
        """
        导出文档到本地

        :param book:        知识库对象
        :param doc:         文档对象
        :param save_path:   保存路径
        :param retry:       重试次数
        :return:            是否成功
        """
        context = format_doc_context(book, doc)
        if retry <= 0:
            logger.error("[export] 重试次数必须大于0 %s retry=%s", context, retry)
            return False

        export_format = get_export_format()
        export_payload = get_export_payload(export_format)
        export_url = f"{self.base_url}/api/docs/{doc.id}/export"

        for attempt in range(1, retry + 1):
            logger.info(
                "[export] 发起导出请求 %s format=%s attempt=%s/%s",
                context,
                export_format,
                attempt,
                retry,
            )

            try:
                response = self._requestSession.post(
                    export_url,
                    json=export_payload,
                    headers=self._build_export_headers(),
                )
            except Exception as exc:
                logger.warning(
                    "[export] 请求异常 %s attempt=%s/%s error=%s",
                    context,
                    attempt,
                    retry,
                    exc,
                )
                continue

            if response.status_code != 200:
                if self._is_unpublished_export(response):
                    logger.warning("[export] 文档未发布，跳过导出 %s", context)
                    return False

                if response.status_code == 404:
                    logger.warning("[export] 文档不存在，跳过导出 %s", context)
                    return False

                logger.warning(
                    "[export] 导出请求失败 %s status=%s attempt=%s/%s",
                    context,
                    response.status_code,
                    attempt,
                    retry,
                )
                continue

            try:
                response_data = response.json()
            except json.JSONDecodeError as exc:
                logger.warning(
                    "[export] 导出响应 JSON 解析失败 %s attempt=%s/%s error=%s",
                    context,
                    attempt,
                    retry,
                    exc,
                )
                continue

            export_data = response_data.get("data")
            if not isinstance(export_data, dict):
                logger.warning(
                    "[export] 导出响应缺少 data 字段 %s attempt=%s/%s",
                    context,
                    attempt,
                    retry,
                )
                continue

            state = export_data.get("state")
            if state == "pending":
                logger.info(
                    "[export] 文档导出处理中 %s wait=%ss",
                    context,
                    EXPORT_PENDING_WAIT_SECONDS,
                )
                await asyncio.sleep(EXPORT_PENDING_WAIT_SECONDS)
                continue

            if state == "error":
                logger.error("[export] 服务端导出失败 %s", context)
                return False

            download_url = export_data.get("url")
            if not download_url:
                logger.warning(
                    "[export] 导出响应缺少下载链接 %s attempt=%s/%s",
                    context,
                    attempt,
                    retry,
                )
                continue

            if download_url.startswith("/"):
                download_url = self.base_url + download_url

            try:
                download_response = self._requestSession.get(download_url)
            except Exception as exc:
                logger.warning(
                    "[export] 下载请求异常 %s attempt=%s/%s error=%s",
                    context,
                    attempt,
                    retry,
                    exc,
                )
                continue

            if download_response.status_code == 422:
                logger.info(
                    "[export] 下载资源未就绪 %s wait=%ss",
                    context,
                    EXPORT_PENDING_WAIT_SECONDS,
                )
                await asyncio.sleep(EXPORT_PENDING_WAIT_SECONDS)
                continue

            if download_response.status_code != 200:
                logger.warning(
                    "[export] 下载失败 %s status=%s attempt=%s/%s",
                    context,
                    download_response.status_code,
                    attempt,
                    retry,
                )
                continue

            if export_format == "pdf":
                saved = self._save_pdf_export(
                    download_response.content, save_path, context
                )
            else:
                download_response.encoding = download_response.apparent_encoding
                saved = await self._save_markdown_export(
                    book, doc, download_response.text, save_path, context
                )

            if saved:
                logger.info(
                    "[export] 导出成功 %s format=%s path=%s",
                    context,
                    export_format,
                    save_path,
                )
                return True

            logger.warning(
                "[export] 文件保存失败，将重试 %s attempt=%s/%s",
                context,
                attempt,
                retry,
            )

        logger.error(
            "[export] 导出失败，达到最大重试次数 %s retries=%s", context, retry
        )
        return False

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
        api = "/api/mine/group_quick_links"
        url = self.base_url + api

        response = self._requestSession.get(url)
        response.raise_for_status()
        return QuickLinksData(response.json()["data"])

    async def groups(self) -> list[YuqueGroup]:
        params = {
            "offset": 0,
            "limit": 200,
        }
        api = "/api/mine/groups"
        url = self.base_url + api

        response = self._requestSession.get(url, params=params)
        response.raise_for_status()
        return [YuqueGroup(i) for i in response.json()["data"]]


async def download_all():
    """下载所有语雀文档"""
    cfg = get_config()
    yuque = Yuque()
    save_base_path = cfg["save_path"]
    export_format = cfg.get("export_format", "pdf")

    if not yuque.is_initialized:
        logger.error("[download] 客户端初始化失败，终止下载")
        return False

    stats = {
        "books": 0,
        "docs": 0,
        "success": 0,
        "skip": 0,
        "fail": 0,
    }

    try:
        versions = await load_document_versions()
        logger.info("[download] 开始下载全部文档")

        books = await yuque.books()
        stats["books"] = len(books)
        logger.info("[download] 知识库数量 count=%s", stats["books"])

        for book in books:
            book_context = format_book_context(book)
            try:
                docs = await yuque.docs(book)
                stats["docs"] += len(docs)

                export_tasks, skip_count = await build_book_export_tasks(
                    book=book,
                    docs=docs,
                    versions=versions,
                    save_base_path=save_base_path,
                    export_format=export_format,
                )
                stats["skip"] += skip_count

                if not export_tasks:
                    logger.info("[download] 无需下载 %s", book_context)
                    continue

                results = await export_book_docs(yuque, book, export_tasks)
                versions, success_count, fail_count = await apply_export_results(
                    book=book,
                    export_tasks=export_tasks,
                    results=results,
                    versions=versions,
                )

                stats["success"] += success_count
                stats["fail"] += fail_count

                await save_document_versions(versions)
            except Exception as exc:
                logger.exception(
                    "[download] 处理知识库失败 %s error=%s", book_context, exc
                )

        await save_document_versions(versions)
        logger.info(
            "[download] 任务完成 books=%s docs=%s success=%s skip=%s fail=%s",
            stats["books"],
            stats["docs"],
            stats["success"],
            stats["skip"],
            stats["fail"],
        )
        return True
    except Exception as exc:
        logger.exception("[download] 下载过程中发生错误 error=%s", exc)
        return False


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
        except Exception as exc:
            logger.error(
                "[version] 加载版本文件失败 path=%s error=%s", version_file, exc
            )
    return {}


async def save_document_versions(versions):
    """保存文档版本信息"""
    version_file = get_version_file_path()
    try:
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as exc:
        logger.error("[version] 保存版本文件失败 path=%s error=%s", version_file, exc)
        return False


async def check_document_updates(book: YuqueBook, doc: YuqueDocs, versions: dict):
    """检查文档是否有更新"""
    doc_key = f"{book.id}_{doc.id}"

    current_version = versions.get(doc_key, {})
    current_updated_at = current_version.get("updated_at", "")
    return doc.updated_at > current_updated_at


async def update_document_version(versions, book: YuqueBook, doc: YuqueDocs):
    """更新文档版本信息"""
    doc_key = f"{book.id}_{doc.id}"
    versions[doc_key] = {
        "book_id": book.id,
        "book_name": book.name,
        "doc_id": doc.id,
        "doc_title": doc.title,
        "updated_at": doc.updated_at,
        "last_check_time": datetime.datetime.now().isoformat(),
    }
    return versions


async def build_book_export_tasks(
    book: YuqueBook,
    docs: list[YuqueDocs],
    versions: dict,
    save_base_path: str,
    export_format: str,
) -> tuple[list[tuple[YuqueDocs, str]], int]:
    """构建单个知识库的导出任务。"""
    export_tasks = []
    skip_count = 0

    for doc in docs:
        if doc.type != "Doc":
            skip_count += 1
            continue

        save_path = build_doc_save_path(save_base_path, book, doc, export_format)
        if not os.path.exists(save_path):
            export_tasks.append((doc, save_path))
            continue

        has_update = await check_document_updates(book, doc, versions)
        if not has_update:
            skip_count += 1
            continue

        logger.info(
            "[download] 文档有更新，准备重新下载 %s", format_doc_context(book, doc)
        )
        export_tasks.append((doc, save_path))

    return export_tasks, skip_count


async def export_book_docs(
    yuque: Yuque, book: YuqueBook, export_tasks: list[tuple[YuqueDocs, str]]
) -> list:
    """并发导出单个知识库下的文档。"""
    if not export_tasks:
        return []

    max_workers = min(MAX_EXPORT_WORKERS, len(export_tasks))
    logger.info(
        "[download] 开始并发导出 %s tasks=%s workers=%s",
        format_book_context(book),
        len(export_tasks),
        max_workers,
    )

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            loop.run_in_executor(executor, run_doc_export_sync, yuque, book, doc, path)
            for doc, path in export_tasks
        ]
        return await asyncio.gather(*futures, return_exceptions=True)


async def apply_export_results(
    book: YuqueBook,
    export_tasks: list[tuple[YuqueDocs, str]],
    results: list,
    versions: dict,
) -> tuple[dict, int, int]:
    """统计导出结果并更新版本信息。"""
    success_count = 0
    fail_count = 0

    for (doc, _), result in zip(export_tasks, results):
        context = format_doc_context(book, doc)

        if isinstance(result, Exception):
            fail_count += 1
            logger.error("[download] 导出任务异常 %s error=%s", context, result)
            continue

        if result:
            versions = await update_document_version(versions, book, doc)
            success_count += 1
            logger.info("[download] 下载成功 %s", context)
            continue

        fail_count += 1
        logger.warning("[download] 下载失败 %s", context)

    return versions, success_count, fail_count


async def monitor_updates():
    """监控文档更新并下载"""
    cfg = get_config()
    yuque = Yuque()
    save_base_path = cfg["save_path"]
    export_format = cfg.get("export_format", "pdf")

    if not yuque.is_initialized:
        logger.error("[monitor] 客户端初始化失败，终止监控")
        return False

    versions = await load_document_versions()
    logger.info("[monitor] 开始监控更新 at=%s", datetime.datetime.now().isoformat())

    try:
        books = await yuque.books()
        update_count = 0
        fail_count = 0

        for book in books:
            book_context = format_book_context(book)
            try:
                docs = await yuque.docs(book)
                docs.sort(key=lambda d: d.updated_at, reverse=True)

                for doc in docs:
                    if doc.type != "Doc":
                        continue

                    try:
                        context = format_doc_context(book, doc)
                        has_update = await check_document_updates(book, doc, versions)
                        if not has_update:
                            continue

                        save_path = build_doc_save_path(
                            save_base_path, book, doc, export_format
                        )
                        export_success = await yuque.docs_export(book, doc, save_path)
                        if export_success:
                            versions = await update_document_version(
                                versions, book, doc
                            )
                            update_count += 1
                            logger.info("[monitor] 更新成功 %s", context)
                        else:
                            fail_count += 1
                            logger.warning("[monitor] 更新失败 %s", context)
                    except Exception as exc:
                        fail_count += 1
                        logger.exception(
                            "[monitor] 处理文档失败 %s error=%s",
                            format_doc_context(book, doc),
                            exc,
                        )

            except Exception as exc:
                logger.exception(
                    "[monitor] 获取知识库文档失败 %s error=%s", book_context, exc
                )

        await save_document_versions(versions)
        logger.info(
            "[monitor] 监控完成 updates=%s fail=%s at=%s",
            update_count,
            fail_count,
            datetime.datetime.now().isoformat(),
        )
        return True

    except Exception as exc:
        logger.exception("[monitor] 监控更新过程中发生错误 error=%s", exc)
        return False


async def download_and_monitor(interval_minutes=60):
    """下载所有文档并持续监控更新"""
    get_config()

    try:
        logger.info("[monitor] 首次运行，执行全量下载")
        await download_all()

        while True:
            try:
                await monitor_updates()
                logger.info(
                    "[monitor] 等待下次检查 interval_minutes=%s", interval_minutes
                )
                await asyncio.sleep(interval_minutes * 60)
            except Exception as exc:
                logger.error("[monitor] 监控循环异常 error=%s", exc)
                logger.info("[monitor] 等待60秒后重试")
                await asyncio.sleep(60)
    except Exception as exc:
        logger.exception("[monitor] 程序运行异常 error=%s", exc)
        logger.info("[monitor] 程序将退出，请检查错误原因后重启")
