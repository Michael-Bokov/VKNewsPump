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
    
class VKPublishTool(BaseTool):
    name: str = "publish_to_vk"
    description: str = "Публикует пост в группе VK. Требует настройки токена и group_id."
    args_schema: Type[BaseModel] = VKPublishInput
        
    def _run(
        self,
        post_text: str,
        article_url: Optional[str] = None,
        image_path: Optional[str] = None,
        #schedule_time: Optional[int] = None
    ) -> str:
        """Публикует пост в VK"""
               
        try:
            token = os.getenv('VK_ACCESS_TOKEN')
            group_id = os.getenv('VK_GROUP_ID')
            if not token or not group_id:
                return "❌ Ошибка: не заданы VK_ACCESS_TOKEN или VK_GROUP_ID в окружении"
            publisher = VKPublisher(access_token=token, group_id=int(group_id))
            # Если указан свой путь к изображению, временно меняем
            original_image_path = None
            if image_path:
                original_image_path = publisher.image_path
                publisher.image_path = Path(image_path)
            
            # # Публикуем пост
            # if schedule_time:
            #     result = self._publish_scheduled(post_text, article_url, schedule_time)
            # else:
            post_id = publisher.publish_post(post_text, article_url)
            # Восстанавливаем путь к изображению если меняли
            if original_image_path:
                publisher.image_path = original_image_path
            if post_id:
                group_abs = abs(int(group_id))
                post_url = f"https://vk.com/wall-{group_abs}_{post_id}"
                return (f"✅ Пост успешно опубликован в VK!\n"
                        f"📝 ID поста: {post_id}\n"
                        f"🔗 Ссылка: {post_url}\n"
                        f"📏 Длина: {len(post_text)} символов\n"
                        f"👥 Группа ID: {group_id}")
            else:
                return "❌ Не удалось опубликовать пост в VK"
        except Exception as e:
            return f"❌ Ошибка публикации в VK: {str(e)}"
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
    
       
    return [VKPublishTool(vk_publisher=vk_publisher)]#tools