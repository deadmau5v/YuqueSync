class YuqueBook:
    """
    语雀知识库对象模型
    """
    def __init__(self, data: dict):
        self.id: int = data.get('id')  # 知识库ID
        self.name: str = data.get('name')  # 知识库名称
        self.slug: str = data.get('slug')  # 知识库路径
        self.description: str = data.get('description', '')  # 知识库描述
        self.type: str = data.get('type')  # 类型，如 Book
        self.layout: str = data.get('layout')  # 布局
        self.public: int = data.get('public', 0)  # 是否公开，0表示私密
        self.items_count: int = data.get('items_count', 0)  # 文档数量
        self.likes_count: int = data.get('likes_count', 0)  # 点赞数
        self.read_count = data.get('read_count')  # 阅读数
        self.creator_id: int = data.get('creator_id')  # 创建者ID
        self.organization_id: int = data.get('organization_id')  # 组织ID
        self.created_at: str = data.get('created_at')  # 创建时间
        self.updated_at: str = data.get('updated_at')  # 更新时间
        self.content_updated_at: str = data.get('content_updated_at')  # 内容更新时间
        self.archived_at = data.get('archived_at')  # 归档时间
        self.cover: str = data.get('cover')  # 封面URL
        self.cover_color: str = data.get('cover_color')  # 封面颜色
        self.abilities: dict = data.get('abilities', {})  # 权限设置，如 {create_doc: true, modify_setting: false, destroy: false, share: true, read_private: true}
        self.enable_announcement: bool = data.get('enable_announcement', False)  # 是否启用公告
        self.enable_auto_publish: bool = data.get('enable_auto_publish', False)  # 是否启用自动发布
        self.enable_automation: bool = data.get('enable_automation', False)  # 是否启用自动化
        self.doc_create_location: str = data.get('doc_create_location')  # 文档创建位置，如 top
        self.doc_typography: str = data.get('doc_typography')  # 文档排版，如 classic_all
        self.doc_viewport: str = data.get('doc_viewport')  # 文档视口，如 fixed
        
    def __str__(self):
        return f"YuqueBook(id={self.id}, name={self.name}, slug={self.slug}, description={self.description.replace(chr(10), '')}, type={self.type}, updated_at={self.updated_at})"

    def __repr__(self):
        return self.__str__()


class YuqueDocs:
    """
    语雀文档对象模型
    """
    def __init__(self, data: dict):
        self.id: int = data.get('id')  # 文档ID
        self.slug: str = data.get('slug')  # 文档路径
        self.title: str = data.get('title')  # 文档标题
        self.book_id: int = data.get('book_id')  # 所属知识库ID
        self.description: str = data.get('description', '')  # 文档描述
        self.custom_description: str = data.get('custom_description', '')  # 自定义描述
        self.format: str = data.get('format')  # 格式，如 lake
        self.public: int = data.get('public', 0)  # 公开级别
        self.status: int = data.get('status', 0)  # 状态
        self.view_status: int = data.get('view_status', 0)  # 查看状态
        self.read_status: int = data.get('read_status', 0)  # 阅读状态
        self.likes_count: int = data.get('likes_count', 0)  # 点赞数
        self.comments_count: int = data.get('comments_count', 0)  # 评论数
        self.word_count: int = data.get('word_count', 0)  # 字数
        self.read_count = data.get('read_count')  # 阅读数
        self.cover: str = data.get('cover')  # 封面URL
        self.user_id: int = data.get('user_id')  # 创建者ID
        self.last_editor_id: int = data.get('last_editor_id')  # 最后编辑者ID
        self.space_id: int = data.get('space_id', 0)  # 空间ID
        self.region: str = data.get('region')  # 区域
        self.type: str = data.get('type')  # 类型，如 Doc
        self.sub_type = data.get('sub_type')  # 子类型
        self.created_at: str = data.get('created_at')  # 创建/时间
        self.updated_at: str = data.get('updated_at')  # 更新时间
        self.published_at: str = data.get('published_at')  # 发布时间
        self.first_published_at: str = data.get('first_published_at')  # 首次发布时间
        self.content_updated_at: str = data.get('content_updated_at')  # 内容更新时间
        self.pinned_at = data.get('pinned_at')  # 置顶时间
        self.selected_at = data.get('selected_at')  # 精选时间
        self.draft_version: int = data.get('draft_version', 0)  # 草稿版本
        self.editor_meta: str = data.get('editor_meta', '')  # 编辑元数据
        self.editor_meta_draft: str = data.get('editor_meta_draft', '')  # 草稿编辑元数据
        self.title_draft = data.get('title_draft')  # 草稿标题
        self.tag = data.get('tag')  # 标签
        self.book = data.get('book')  # 所属知识库
        self.user = data.get('user')  # 创建者
        self.last_editor = data.get('last_editor')  # 最后编辑者
        self.share = data.get('share')  # 分享信息
        self.meta: dict = data.get('meta', {})  # 元数据
        self.privacy_migrated: bool = data.get('privacy_migrated', False)  # 隐私迁移
        self._serializer: str = data.get('_serializer', '')  # 序列化器
    
    def __str__(self):
        return f"YuqueDocs(id={self.id}, title={self.title}, slug={self.slug}, type={self.type}, updated_at={self.updated_at})"
    
    def __repr__(self):
        return self.__str__()

class YuqueContributor:
    """
    语雀文档贡献者模型
    """
    def __init__(self, data: dict):
        self.id: int = data.get('id')  # 用户ID
        self.type: str = data.get('type')  # 用户类型，如 User
        self.login: str = data.get('login')  # 登录名
        self.name: str = data.get('name')  # 用户名称
        self.description: str = data.get('description', '')  # 用户描述
        self.avatar: str = data.get('avatar')  # 头像URL
        self.avatar_url: str = data.get('avatar_url')  # 头像URL
        self.followers_count: int = data.get('followers_count', 0)  # 粉丝数
        self.following_count: int = data.get('following_count', 0)  # 关注数
        self.role: int = data.get('role', 0)  # 角色
        self.status: int = data.get('status', 0)  # 状态
        self.public: int = data.get('public', 0)  # 公开级别
        self.created_at: str = data.get('created_at')  # 创建时间
        self.updated_at: str = data.get('updated_at')  # 更新时间
        self.isPaid: bool = data.get('isPaid', False)  # 是否付费
        self.member_level: int = data.get('member_level', 0)  # 会员等级
        self.identity: int = data.get('identity', 0)  # 身份
        
    def __str__(self):
        return f"YuqueContributor(id={self.id}, name={self.name}, login={self.login})"
    
    def __repr__(self):
        return self.__str__()

class YuqueDocDetail:
    """
    语雀文档详情模型
    """
    def __init__(self, data: dict):
        self.word_count: int = data.get('wordCount', 0)  # 文档字数
        self.contributors: list[YuqueContributor] = [YuqueContributor(c) for c in data.get('contributors', [])]  # 贡献者列表
        self.enable_custom_body: bool = data.get('enableCustomBody', False)  # 是否启用自定义正文
        self.enable_catalog: bool = data.get('enableCatalog', False)  # 是否启用目录
        self.order: str = data.get('order', '')  # 排序方式
        self.layout: str = data.get('layout', '')  # 布局方式
        self.enable_user_feed: bool = data.get('enableUserFeed', False)  # 是否启用用户反馈
        
        # 自定义索引
        custom_index = data.get('customIndex', {})
        if custom_index:
            self.custom_index_id: int = custom_index.get('id')
            self.custom_index_status: int = custom_index.get('status')
            self.custom_index_type: str = custom_index.get('type')
            self.custom_index_body: str = custom_index.get('body', '')
            self.custom_index_created_at: str = custom_index.get('created_at')
            self.custom_index_updated_at: str = custom_index.get('updated_at')
    
    def __str__(self):
        return f"YuqueDocDetail(word_count={self.word_count}, contributors_count={len(self.contributors)})"
    
    def __repr__(self):
        return self.__str__()


class QuickLinksData:
    def __init__(self, data: dict):
        self.groups = []

        for group_data in data:
            group = QuickLinkGroup(group_data)
            self.groups.append(group)
    
    def __str__(self):
        return f"QuickLinksData(groups_count={len(self.groups)})"
    
    def __repr__(self):
        return self.__str__()


class QuickLinkGroup:
    """
    语雀快速链接组模型
    """
    def __init__(self, data: dict):
        self.id = data.get('id')  # 快速链接组ID
        self.user_id = data.get('user_id')  # 用户ID
        self.organization_id = data.get('organization_id')  # 组织ID
        self.type = data.get('type')  # 类型，如 Group
        self.icon = data.get('icon')  # 图标
        self.title = data.get('title')  # 标题
        self.url = data.get('url')  # URL路径
        self.order_num = data.get('order_num')  # 排序序号
        self.target_id = data.get('target_id')  # 目标ID
        self.target_type = data.get('target_type')  # 目标类型，如 User
        self.created_at = data.get('created_at')  # 创建时间
        self.updated_at = data.get('updated_at')  # 更新时间
        self.ref_id = data.get('ref_id')  # 引用ID，如 dashboard_groups
        
        # 解析target对象
        target_data = data.get('target', {})
        if target_data:
            self.target = QuickLinkTarget(target_data)
        else:
            self.target = None
            
        # 解析user对象
        user_data = data.get('user', {})
        if user_data:
            self.user = QuickLinkUser(user_data)
        else:
            self.user = None
    
    def __str__(self):
        status = "未读" if self.user and self.user.hasActivities else "已读"
        return f"QuickLinkGroup(id={self.id}, title={self.title}, status={status})"
    
    def __repr__(self):
        return self.__str__()


class QuickLinkTarget:
    """
    语雀快速链接目标模型
    """
    def __init__(self, data: dict):
        self.id = data.get('id')  # 目标ID
        self.type = data.get('type')  # 目标类型，如 Group
        self.login = data.get('login')  # 登录名
        self.name = data.get('name')  # 名称
        self.description = data.get('description')  # 描述
        self.avatar = data.get('avatar')  # 头像
        self.avatar_url = data.get('avatar_url')  # 头像URL
        self.books_count = data.get('books_count')  # 知识库数量
        self.public_books_count = data.get('public_books_count')  # 公开知识库数量
        self.members_count = data.get('members_count')  # 成员数量
        self.public = data.get('public')  # 公开级别
        self.scene = data.get('scene')  # 场景，如 group-type-project
        self.created_at = data.get('created_at')  # 创建时间
        self.updated_at = data.get('updated_at')  # 更新时间
        self.isPaid = data.get('isPaid')  # 是否付费
        
    def __str__(self):
        return f"QuickLinkTarget(id={self.id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()


class QuickLinkUser:
    """
    语雀快速链接用户模型
    """
    def __init__(self, data: dict):
        self.id = data.get('id')  # 用户ID
        self.type = data.get('type')  # 用户类型，如 User
        self.login = data.get('login')  # 登录名
        self.name = data.get('name')  # 用户名称
        self.avatar = data.get('avatar')  # 头像
        self.avatar_url = data.get('avatar_url')  # 头像URL
        self.role = data.get('role')  # 角色
        self.isPaid = data.get('isPaid')  # 是否付费
        self.description = data.get('description')  # 描述
        self.hasActivities = data.get('hasActivities')
        
    def __str__(self):
        return f"QuickLinkUser(id={self.id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()
    

class YuqueGroup:
    """
    语雀组
    """
    def __init__(self, data: dict):
        self.id = data.get('id')  # 组ID
        self.type = data.get('type')  # 类型，如 Group
        self.login = data.get('login')  # 登录名
        self.name = data.get('name')  # 组名称
        self.description = data.get('description')  # 描述
        self.avatar = data.get('avatar')  # 头像
        self.avatar_url = data.get('avatar_url')  # 头像URL
        self.books_count = data.get('books_count')  # 知识库数量
        self.public_books_count = data.get('public_books_count')  # 公开知识库数量
        self.members_count = data.get('members_count')  # 成员数量
        self.public = data.get('public')  # 公开级别
        self.scene = data.get('scene')  # 场景
        self.created_at = data.get('created_at')  # 创建时间
        self.updated_at = data.get('updated_at')  # 更新时间
        self.isPaid = data.get('isPaid')  # 是否付费
        self.organization_id = data.get('organization_id')  # 组织ID
        self.owner_id = data.get('owner_id')  # 拥有者ID
        self.status = data.get('status')  # 状态
        self.group_user_role = data.get('group_user_role')  # 用户在组中的角色
        self.group_user_id = data.get('group_user_id')  # 用户在组中的ID
        self.group_user_joined_at = data.get('group_user_joined_at')  # 用户加入组的时间
        self.isPublicPage = data.get('isPublicPage')  # 是否公开页面
        self.isWiki = data.get('isWiki')  # 是否是Wiki
        self.topics_count = data.get('topics_count')  # 主题数量
        
    def __str__(self):
        return f"YuqueGroup(id={self.id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()
    
class YuqueActivities:
    """组更新动态"""
    def __init__(self, data: dict):
        self.id = data.get('id')  # 动态ID
        self.type = data.get('type')  # 类型，如 updateDoc
        self.actor_id = data.get('actor_id')  # 操作者ID
        self.user_id = data.get('user_id')  # 用户ID
        self.book_id = data.get('book_id')  # 知识库ID
        self.target_type = data.get('target_type')  # 目标类型，如 Doc
        self.target_count = data.get('target_count')  # 目标数量
        self.targets = data.get('targets')  # 目标列表
        self.created_at = data.get('created_at')  # 创建时间
        self.updated_at = data.get('updated_at')  # 更新时间
        self.actor = data.get('actor')  # 操作者信息
        self.book = data.get('book')  # 知识库信息
        self.user = data.get('user')  # 用户信息
        
    def __str__(self):
        return f"YuqueActivities(id={self.id}, type={self.type})"
    
    def __repr__(self):
        return self.__str__()