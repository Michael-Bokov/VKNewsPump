#publisher_tool.py
 
# vk_tool.py
from typing import Type, Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from direct_publisher_agent import VKPublisher
import json
import os
from pathlib import Path

class VKPublishInput(BaseModel):
    """Входные данные для публикации поста в VK"""
    post_text: str = Field(description="Текст поста для публикации в VK")
    article_url: Optional[str] = Field(
        default=None,
        description="URL статьи для добавления в пост (опционально)"
    )
    image_path: Optional[str] = Field(
        default=None,
        description="Путь к изображению для поста (опционально)"
    )
    # schedule_time: Optional[int] = Field(
    #     default=None,
    #     description="Unix timestamp для отложенной публикации (опционально)"
    # )

# class VKArticlePublishInput(BaseModel):
#     """Входные данные для публикации статьи в VK"""
#     article_data: str = Field(description="Данные статьи в формате JSON строки")
#     use_image: bool = Field(
#         default=True,
#         description="Использовать ли изображение по умолчанию"
#     )
#     schedule_time: Optional[int] = Field(
#         default=None,
#         description="Unix timestamp для отложенной публикации"
#     )

class VKPublishTool(BaseTool):
    name: str = "publish_to_vk"
    description: str = "Публикует пост в группе VK. Требует настройки токена и group_id."
    args_schema: Type[BaseModel] = VKPublishInput
    #publisher: Optional[VKPublisher] = None 
    # Используем PrivateAttr для кастомных полей
    _publisher: VKPublisher = PrivateAttr()
    #_vk_session: Any = PrivateAttr()

    def __init__(
        self,
        access_token: Optional[str] = None,
        group_id: Optional[int] = None,
        vk_publisher: Optional[VKPublisher] = None
    ):
        super().__init__()
        
        if vk_publisher:
            self._publisher = vk_publisher
        elif access_token and group_id:
            self._publisher = VKPublisher(access_token=access_token, group_id=group_id)
        else:
            # Пробуем получить из переменных окружения
            token = os.getenv('VK_ACCESS_TOKEN')
            gid = os.getenv('VK_GROUP_ID')
            
            if token and gid:
                self._publisher = VKPublisher(access_token=token, group_id=int(gid))
            else:
                raise ValueError(
                    "Необходимо указать access_token и group_id или установить "
                    "VK_ACCESS_TOKEN и VK_GROUP_ID в переменных окружения"
                )
    # @property
    # def publisher(self):
    #     """Getter для обратной совместимости"""
    #     return self._publisher
    
    def _run(
        self,
        post_text: str,
        article_url: Optional[str] = None,
        image_path: Optional[str] = None,
        #schedule_time: Optional[int] = None
    ) -> str:
        """Публикует пост в VK"""
        try:
            # Если указан свой путь к изображению, временно меняем
            original_image_path = None
            if image_path:
                original_image_path = self._publisher.image_path
                self._publisher.image_path = Path(image_path)
            
            # # Публикуем пост
            # if schedule_time:
            #     result = self._publish_scheduled(post_text, article_url, schedule_time)
            # else:
            post_id = self._publisher.publish_post(post_text, article_url)
            result = self._format_result(post_id, post_text)
            
            # Восстанавливаем путь к изображению если меняли
            if original_image_path:
                self._publisher.image_path = original_image_path
            
            return result
            
        except Exception as e:
            return f"❌ Ошибка публикации в VK: {str(e)}"
    
    # async def _arun(
    #     self,
    #     post_text: str,
    #     article_url: Optional[str] = None,
    #     image_path: Optional[str] = None,
    #     schedule_time: Optional[int] = None
    # ) -> str:
    #     """Асинхронная публикация"""
    #     try:
    #         import asyncio
    #         return await asyncio.to_thread(
    #             self._run,
    #             post_text,
    #             article_url,
    #             image_path,
    #             schedule_time
    #         )
    #     except Exception as e:
    #         return f"❌ Ошибка публикации в VK: {str(e)}"
    
    # def _publish_scheduled(
    #     self,
    #     post_text: str,
    #     article_url: Optional[str],
    #     schedule_time: int
    # ) -> str:
    #     """Отложенная публикация (упрощенная реализация)"""
    #     try:
    #         from datetime import datetime
            
    #         schedule_dt = datetime.fromtimestamp(schedule_time)
            
    #         post_id = self.publisher.publish_post(post_text, article_url)
            
    #         return (
    #             f"✅ Пост опубликован немедленно (ID: {post_id})\n"
    #             f"⏰ Запланированная дата была: {schedule_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
    #             f"ℹ️ Для отложенной публикации используйте VK API напрямую"
    #         )
            
    #     except Exception as e:
    #         return f"❌ Ошибка при отложенной публикации: {str(e)}"
    
    def _format_result(self, post_id: Optional[int], post_text: str) -> str:
        """Форматирует результат публикации"""
        if post_id:
            group_id = abs(self._publisher.group_id)
            post_url = f"https://vk.com/wall-{group_id}_{post_id}"
            
            return (
                f"✅ Пост успешно опубликован в VK!\n"
                f"📝 ID поста: {post_id}\n"
                f"🔗 Ссылка: {post_url}\n"
                f"📏 Длина: {len(post_text)} символов\n"
                f"👥 Группа ID: {self._publisher.group_id}"
            )
        else:
            return "❌ Не удалось опубликовать пост в VK"


# class VKArticlePublisherTool(BaseTool):
#     """Инструмент для публикации статьи в VK"""
#     name: str = "publish_article_to_vk"
#     description: str = "Публикует статью (с заголовком и текстом) в группе VK"
#     args_schema: Type[BaseModel] = VKArticlePublishInput
    
#     def __init__(self, vk_publish_tool: VKPublishTool):
#         super().__init__()
#         self.vk_tool = vk_publish_tool
    
#     def _run(
#         self,
#         article_data: str,
#         use_image: bool = True,
#         schedule_time: Optional[int] = None
#     ) -> str:
#         """Публикует статью в VK"""
#         try:
#             # Парсим данные статьи
#             article = json.loads(article_data)
            
#             # Извлекаем пост и URL
#             post_text = article.get('vk_post', '')
#             article_url = article.get('url', '')
            
#             if not post_text:
#                 # Если нет готового поста, создаем из заголовка и текста
#                 title = article.get('title_ru', article.get('title', 'Новая статья'))
#                 text = article.get('text_ru', article.get('full_text', ''))
                
#                 post_text = self._create_post_from_article(title, text[:500])
            
#             # Определяем путь к изображению
#             image_path = None
#             if use_image and hasattr(self.vk_tool.publisher, 'image_path'):
#                 image_path = str(self.vk_tool.publisher.image_path)
            
#             # Публикуем через основной инструмент
#             return self.vk_tool._run(
#                 post_text=post_text,
#                 article_url=article_url,
#                 image_path=image_path,
#                 schedule_time=schedule_time
#             )
            
#         except json.JSONDecodeError:
#             return "❌ Ошибка: Некорректный JSON формат статьи"
#         except Exception as e:
#             return f"❌ Ошибка публикации статьи: {str(e)}"
    
#     def _create_post_from_article(self, title: str, text: str) -> str:
#         """Создает пост из статьи если нет готового"""
#         return f"""🤖 {title}

# {text[:300]}...

# Читать полностью: [ссылка в статье]

# #Новости #Технологии #ИИ"""


# class VKStatsTool(BaseTool):
#     """Инструмент для получения статистики VK"""
#     name: str = "get_vk_stats"
#     description: str = "Получает базовую статистику группы VK (требует токен с правами stats)"
    
#     def __init__(self, access_token: str, group_id: int):
#         super().__init__()
#         self.publisher = VKPublisher(access_token=access_token, group_id=group_id)
    
#     def _run(self, period: str = "week") -> str:
#         """Получает статистику группы"""
#         try:
#             # Поддерживаемые периоды
#             valid_periods = {
#                 'day': 1,
#                 'week': 7,
#                 'month': 30,
#                 'year': 365
#             }
            
#             if period not in valid_periods:
#                 return f"⚠️ Неподдерживаемый период. Используйте: {', '.join(valid_periods.keys())}"
            
#             # Пытаемся получить статистику
#             try:
#                 # Получаем информацию о группе
#                 group_info = self.publisher.vk.groups.getById(
#                     group_id=abs(self.publisher.group_id),
#                     fields='members_count,description'
#                 )
                
#                 # Получаем последние посты
#                 posts = self.publisher.vk.wall.get(
#                     owner_id=self.publisher.group_id,
#                     count=10
#                 )
                
#                 # Базовая статистика
#                 stats = {
#                     "group_name": group_info[0]['name'] if group_info else "Неизвестно",
#                     "members_count": group_info[0].get('members_count', 'Неизвестно'),
#                     "total_posts": posts.get('count', 0),
#                     "last_post_date": "Неизвестно"
#                 }
                
#                 if posts.get('items'):
#                     last_post = posts['items'][0]
#                     stats["last_post_date"] = self._timestamp_to_date(last_post.get('date'))
                
#                 return self._format_stats(stats, period)
                
#             except Exception as api_error:
#                 return f"⚠️ Не удалось получить статистику: {api_error}\nУбедитесь, что токен имеет права stats."
            
#         except Exception as e:
#             return f"❌ Ошибка получения статистики: {str(e)}"
    
#     def _timestamp_to_date(self, timestamp: int) -> str:
#         """Конвертирует timestamp в дату"""
#         from datetime import datetime
#         return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
#     def _format_stats(self, stats: Dict, period: str) -> str:
#         """Форматирует статистику"""
#         lines = [
#             f"📊 Статистика группы VK за {period}:",
#             f"👥 Название: {stats['group_name']}",
#             f"👥 Участников: {stats['members_count']}",
#             f"📝 Всего постов: {stats['total_posts']}",
#             f"⏰ Последний пост: {stats['last_post_date']}",
#             f"🔗 Ссылка: https://vk.com/public{abs(self.publisher.group_id)}",
#             "",
#             "ℹ️ Для подробной статистики используйте VK Ads API или сторонние сервисы"
#         ]
        
#         return "\n".join(lines)


# class VKCheckTool(BaseTool):
#     """Инструмент для проверки подключения к VK"""
#     name: str = "check_vk_connection"
#     description: str = "Проверяет подключение к VK API и доступность группы"
    
#     def __init__(self, access_token: str, group_id: int):
#         super().__init__()
#         self.publisher = VKPublisher(access_token=access_token, group_id=group_id)
    
#     def _run(self) -> str:
#         """Проверяет подключение"""
#         try:
#             # Проверяем токен
#             user_info = self.publisher.vk.users.get()
#             user_id = user_info[0]['id']
            
#             # Проверяем доступ к группе
#             group_info = self.publisher.vk.groups.getById(
#                 group_id=abs(self.publisher.group_id)
#             )
            
#             group_name = group_info[0]['name'] if group_info else "Неизвестно"
            
#             # Пробуем получить права
#             try:
#                 is_admin = self.publisher.vk.groups.isMember(
#                     group_id=str(abs(self.publisher.group_id)),
#                     user_id=user_id
#                 )
#                 admin_status = "✅ Администратор" if is_admin else "⚠️ Не администратор"
#             except:
#                 admin_status = "❓ Не удалось проверить права"
            
#             return (
#                 f"🔗 Подключение к VK API:\n"
#                 f"✅ Токен рабочий (пользователь ID: {user_id})\n"
#                 f"✅ Группа доступна: {group_name} (ID: {self.publisher.group_id})\n"
#                 f"{admin_status}\n\n"
#                 f"ℹ️ Для публикации нужны права администратора или редактора"
#             )
            
#         except Exception as e:
#             return f"❌ Ошибка подключения к VK: {str(e)}\nПроверьте токен и ID группы."


def create_vk_tools(
    access_token: Optional[str] = None,
    group_id: Optional[int] = None,
    vk_publisher: Optional[VKPublisher] = None
) -> List[BaseTool]:
    """Создает все инструменты для работы с VK"""
    
    if not vk_publisher:
        if not access_token or not group_id:
            # Пробуем получить из переменных окружения
            token = os.getenv('VK_ACCESS_TOKEN')
            gid = os.getenv('VK_GROUP_ID')
            
            if not token or not gid:
                raise ValueError(
                    "Для создания инструментов VK укажите access_token и group_id "
                    "или установите VK_ACCESS_TOKEN и VK_GROUP_ID в переменных окружения"
                )
            
            access_token = token
            group_id = int(gid)
    
    # Создаем publisher если не передан
    if not vk_publisher:
        vk_publisher = VKPublisher(access_token=access_token, group_id=group_id)
    
    # # Создаем инструменты
    # publish_tool = VKPublishTool(vk_publisher=vk_publisher)
    # article_tool = VKArticlePublisherTool(vk_publish_tool=publish_tool)
    
    # tools = [
    #     publish_tool,
    #     article_tool,
    # ]
    
    # # Пытаемся добавить инструменты со статистикой
    # try:
    #     stats_tool = VKStatsTool(access_token=access_token, group_id=group_id)
    #     check_tool = VKCheckTool(access_token=access_token, group_id=group_id)
    #     tools.extend([stats_tool, check_tool])
    # except Exception as e:
    #     print(f"⚠️ Не удалось создать дополнительные инструменты VK: {e}")
    
    return [VKPublishTool(vk_publisher=vk_publisher)]#tools