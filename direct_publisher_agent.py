# vk_publisher.py
import vk_api
from vk_api.exceptions import VkApiError
from pathlib import Path
import time
from typing import Dict, Any, Optional
from typing import Optional, Union
import requests
from io import BytesIO


class VKPublisher:
    def __init__(self, access_token: str, group_id: int):
        """
        Инициализация VK API
        :param access_token: Токен доступа VK
        :param group_id: ID группы (со знаком минус для групп)
        """
        self.group_id = -abs(group_id)  # Для групп нужен отрицательный ID
        self.vk_session = vk_api.VkApi(token=access_token)
        self.vk = self.vk_session.get_api()
        self.base_dir = Path(__file__).parent.absolute()
        
        # Путь к изображению
        self.image_path = self.base_dir / "images" / "ai_default_1.jpg"
        # Для загрузки изображений
        self.upload = vk_api.VkUpload(self.vk_session)
    
    def _upload_photo_to_wall(self, image_path: Union[str, Path]) -> Optional[str]:
        """Загружает фото с автоматической конвертацией форматов"""
        try:
            # Конвертируем Path в строку
            image_path_str = str(image_path) if isinstance(image_path, Path) else image_path
            
            print(f"🖼️ Загружаем изображение: {image_path_str}")
            
            # Проверяем файл
            if not Path(image_path_str).exists():
                print(f"❌ Файл не найден: {image_path_str}")
                return None
            
            # Проверяем формат
            try:
                from PIL import Image
                with Image.open(image_path_str) as img:
                    if img.format == 'AVIF':
                        print(f"⚠️ Обнаружен AVIF, конвертируем в JPEG...")
                        # Конвертируем на лету
                        jpeg_path = Path(image_path_str).parent / "temp_converted.jpg"
                        img.convert('RGB').save(jpeg_path, "JPEG", quality=90)
                        image_path_str = str(jpeg_path)
                        print(f"✅ Конвертировано в: {image_path_str}")
            except ImportError:
                print("⚠️ Pillow не установлен, пропускаем проверку формата")
            except Exception as e:
                print(f"⚠️ Ошибка проверки формата: {e}")
            
            # 1. Получаем upload server
            upload_server = self.vk.photos.getWallUploadServer(
                group_id=abs(self.group_id)
            )
            upload_url = upload_server['upload_url']
            print(f"📤 Upload URL получен")
            
            # 2. Загружаем файл ПРАВИЛЬНО
            with open(image_path_str, 'rb') as f:
                # Важно: указываем правильный content-type
                files = {
                    'photo': ('image.jpg', f, 'image/jpeg')
                }
                
                response = requests.post(upload_url, files=files, timeout=30)
            
            result = response.json()
            #print(f"📊 Результат upload: {result}")
            
            # Проверяем результат
            if not result.get('photo'):
                print(f"❌ Ошибка: сервер вернул пустой photo")
                print(f"🔍 Полный ответ сервера: {result}")
                return None
            
            # 3. Сохраняем на сервере VK
            save_result = self.vk.photos.saveWallPhoto(
                group_id=abs(self.group_id),
                server=result['server'],
                photo=result['photo'],
                hash=result['hash']
            )
            
            if save_result and save_result[0]:
                photo_data = save_result[0]
                attachment = f"photo{photo_data['owner_id']}_{photo_data['id']}"
                print(f"✅ Фото загружено, attachment: {attachment}")
                return attachment
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
            return None
    def publish_post(self, post_text: str, article_url: Optional[str] = None) -> Optional[int]:
        """
        Публикует пост в группе VK
        Возвращает ID поста или None в случае ошибки
        """
        try:
            print(f"📤 Публикация поста в VK ({len(post_text)} символов)...")
            post_text += "\nСсылка на источник: "
            attachments = []
            attachments_added = False
            
            # 1. Пробуем загрузить изображение
            photo_attachment = self._upload_photo_to_wall(str(self.image_path))
            
            if photo_attachment:
                attachments.append(photo_attachment)
                attachments_added = True
            else:
                print("ℹ️ Будет опубликован пост без изображения")
            
            # 2. Добавляем ссылку если есть
            if article_url:
                # Проверяем корректность URL
                if article_url.startswith(('http://', 'https://')):
                    # Для ссылок в VK нужно использовать формат "ссылка"
                    attachments.append(article_url)
                    attachments_added = True
                    print(f"🔗 Добавлена ссылка: {article_url}")
                else:
                    print(f"⚠️ Некорректный URL: {article_url}")
            
            # 3. Если нет ни изображения, ни ссылки, добавляем URL в текст
            if not attachments_added and article_url:
                post_text = f"{post_text}\n\n{article_url}"
                print("ℹ️ Ссылка добавлена в текст поста")
            
            # Подготовка параметров
            params = {
                'owner_id': self.group_id,
                'from_group': 1,  # Публикация от имени группы
                'message': post_text,
            }
            
            # Добавляем вложения только если они есть
            if attachments_added and attachments:
                params['attachments'] = ','.join(attachments)
            
            # Проверяем длину текста (VK ограничивает до ~4096 символов)
            if len(post_text) > 4000:
                print(f"⚠️ Текст поста слишком длинный ({len(post_text)} символов), обрезаем до 4000")
                params['message'] = post_text[:4000] + "..."
            
            print(f"📝 Публикую пост с параметрами: owner_id={params['owner_id']}, "
                  f"attachments={params.get('attachments', 'нет')}")
            
            # Публикуем пост
            response = self.vk.wall.post(**params)
            
            post_id = response['post_id']
            print(f"✅ Пост опубликован! ID: {post_id}")
            print(f"🔗 Ссылка: https://vk.com/wall{self.group_id}_{post_id}")
            
            return post_id
            
        except VkApiError as e:
            print(f"❌ Ошибка VK API: {e}")
            # Пробуем опубликовать без вложений
            if attachments_added:
                print("🔄 Пробую опубликовать без вложений...")
                try:
                    params = {
                        'owner_id': self.group_id,
                        'from_group': 1,
                        'message': post_text,
                    }
                    response = self.vk.wall.post(**params)
                    post_id = response['post_id']
                    print(f"✅ Пост опубликован без вложений! ID: {post_id}")
                    return post_id
                except Exception as retry_error:
                    print(f"❌ Ошибка при повторной попытке: {retry_error}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            return None
    
    def publish_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Публикует статью в VK"""
        post_text = article.get('vk_post', '') 
        article_url = article.get('url', '')
        
        if not post_text:
            print("⚠️ Нет текста поста для публикации")
            return article
        
        post_id = self.publish_post(post_text, article_url)
        
        return {
            **article,
            'vk_post_id': post_id,
            'vk_published_at': time.strftime("%Y-%m-%d %H:%M:%S") if post_id else None,
            'vk_published': bool(post_id)
        }