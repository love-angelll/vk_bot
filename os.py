import vk_api
import time
import platform
import psutil
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from config import TOKEN, link_commands, ADMINS  # Импортируем TOKEN, link_commands и список админов ADMINS

# Инициализация сессии
vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

# Функция для отправки сообщения
def send_message(user_id, message):
    vk.messages.send(user_id=user_id, message=message, random_id=0)

# Функция для чтения списка бесед из JSON
def load_chats():
    try:
        with open('chats.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Функция для записи списка бесед в JSON
def save_chats(chats):
    with open('chats.json', 'w', encoding='utf-8') as f:
        json.dump(chats, f, ensure_ascii=False, indent=4)

# Функция для обновления списка бесед без дублирования
def update_chats_list():
    chats = load_chats()
    chat_ids = {chat['chat_id'] for chat in chats}  # Используем set для проверки дублирования по chat_id

    conversations = vk.messages.getConversations(count=50)['items']
    for conversation in conversations:
        chat_settings = conversation['conversation']['chat_settings']
        chat_id = conversation['conversation']['peer']['local_id']
        
        if chat_id not in chat_ids:  # Проверяем, есть ли уже эта беседа в JSON
            creator_id = chat_settings['owner_id']
            title = chat_settings['title']
            avatar_url = chat_settings.get('photo', {}).get('photo_200', 'Нет аватарки')
            
            creator_info = vk.users.get(user_ids=creator_id)[0]
            creator_name = f"{creator_info['first_name']} {creator_info['last_name']}"

            chat_info = {
                "chat_id": chat_id,
                "title": title,
                "creator": creator_name,
                "creator_id": creator_id,
                "link": f"vk.com/chat{chat_id}",
                "avatar_url": avatar_url
            }
            chats.append(chat_info)  # Добавляем новую беседу в список
            chat_ids.add(chat_id)

    save_chats(chats)  # Сохраняем обновленный список бесед

# Функция для вывода списка бесед
def get_chats_list():
    chats = load_chats()
    if not chats:
        return "Нет информации о беседах."
    
    chats_info = "Список бесед, где присутствует бот:\n"
    for index, chat in enumerate(chats, start=1):
        chat_info = (f"{index}. Название беседы: {chat['title']}\n"
                     f"ID беседы: {chat['chat_id']}\n"
                     f"Создатель: {chat['creator']}\n"
                     f"Ссылка на беседу: {chat['link']}\n"
                     f"Аватарка беседы: {chat['avatar_url']}\n")
        chats_info += chat_info + "\n"
    return chats_info

# Функция для получения информации о сервере
def get_server_info():
    try:
        # Получаем системную информацию
        system_info = platform.system()
        python_version = platform.python_version()
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count()
        memory = psutil.virtual_memory()
        memory_used = memory.used / (1024 ** 3)  # В гигабайтах
        memory_total = memory.total / (1024 ** 3)  # В гигабайтах
        disk = psutil.disk_usage('/')
        disk_used = disk.used / (1024 ** 3)  # В гигабайтах
        disk_total = disk.total / (1024 ** 3)  # В гигабайтах

        server_info = (
            f"🚀Информация о сервере🚀\n"
            f"🖥 Система: {system_info}\n"
            f"🐍 Версия питона: {python_version}\n"
            f"📈 Нагрузка ЦП: {cpu_percent}%\n"
            f"📈 Количество ядер: {cpu_cores}\n"
            f"💾 Занятость ОЗУ: {memory_used:.2f}GB из {memory_total:.2f}GB\n"
            f"📗 Загрузка ОЗУ: {memory.percent}%\n"
            f"💽 Диск: {disk_used:.2f}GB из {disk_total:.2f}GB\n"
            f"📀 Диск загружен на: {disk.percent}%"
        )
        return server_info
    except Exception as e:
        return f"Не удалось получить информацию о сервере: {str(e)}"

# Основной цикл бота
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        message_text = event.text.lower()
        user_id = event.user_id

        if message_text == "пинг":
            start_time = time.time()
            response_time = time.time() - start_time
            send_message(user_id, f"ПОНГ БЛ\nВремя ответа: {response_time:.2f} сек.")
        elif message_text == "хост":
            server_info = get_server_info()
            send_message(user_id, server_info)
        elif message_text == "команды":
            send_message(user_id, f"Вот мои команды: {link_commands}")
        elif message_text == "чат":
            chat_info = get_chat_info(event.peer_id - 2000000000)
            send_message(user_id, chat_info)
        elif message_text == "люди":
            chat_members = get_chat_members(event.peer_id - 2000000000)
            send_message(user_id, chat_members)
        elif message_text == "чаты":
            if user_id in ADMINS:
                update_chats_list()  # Обновляем список бесед перед выводом
                chats_list = get_chats_list()
                send_message(user_id, chats_list)
            else:
                send_message(user_id, "У вас нет прав для использования этой команды.")
        else:
            send_message(user_id, "Неизвестная команда")
