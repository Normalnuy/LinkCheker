import os, json, asyncio, re, sys, time
from telethon import TelegramClient
from telethon.tl.types import MessageEntityTextUrl
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.errors.rpcerrorlist import FloodWaitError
from progress.bar import Bar

script_dir = os.path.dirname(sys.argv[0])
config_file_path = os.path.join(script_dir, 'config.json')
session_file_path = os.path.join(script_dir, 'session\\client.session')
links_file_path = os.path.join(script_dir, 'result\\result.txt')

async def main():

    os.system('cls||clear')
    if not os.path.exists(session_file_path):
        
        print("https://my.telegram.org/apps")
        api_id = input("API ID: ")
        api_hash = input("API Hash: ")
        to_config = {'api_id': api_id, 'api_hash': api_hash, 'search_bot': 'en_SearchBot'}
        
        print("Сохранение настроек...")
        with open(config_file_path, 'w') as f:
            f.write(json.dumps(to_config))
        print("Сохранение настроек: Успешно!")
        
        session = False
        while not session:
            print("Создание .session файла...")
            session = await create_session(api_id, api_hash)

    config = get_config()
    await parsing(config)

    print("Нажмите [Ctrl + C] для завершения.")
    while True:
        pass


# ===================================================================================================================== #

async def create_session(api_id, api_hash):
     
     async with TelegramClient(session_file_path, api_id=api_id, api_hash=api_hash) as client:
        
        if await client.is_user_authorized():
            await client.disconnect()
            os.system('cls||clear')
            print("Создание .session файла: Успешно!")
            return True
        else:
            await client.disconnect()
            os.system('cls||clear')
            print("Ошибка: .session не исправен!")
            print("Удаление .session файла...")
            await asyncio.sleep(5)
            os.remove(session_file_path)
            print("Удаление .session файла: Успешно!")
            print("Рестарт авторизации...")
            return False

# ===================================================================================================================== #

async def parsing(config):
    
    input("Убедитесь, что вписали запрос в боте. Если это так - нажмите [Enter]: ")

    api_id = config['api_id']
    api_hash = config['api_hash']
    search_bot = config['search_bot']
    
    async with TelegramClient(session_file_path, api_id=int(api_id), api_hash=api_hash) as client:

        chat = await client.get_entity(f'https://t.me/{search_bot}')

        try:
            message = await get_message(client, chat)
            await client(GetBotCallbackAnswerRequest(
                    chat,
                    message.id,
                    data=message.reply_markup.rows[1].buttons[4].data
                ))
            message = await get_message(client, chat)
        except IndexError:
            print("[IndexError1]: Кнопка не найдена.")
            pass

        pages = get_pages(message.message)

        current_page = pages[0]
        total_pages = pages[1]

        urls = []
        tg_names = []

        bar = Bar("Анализируем ссылки...", max=200)

        for current_page in range(1, total_pages):
            
            message = await get_message(client, chat)
            for entity in message.entities:
                
                if isinstance(entity, MessageEntityTextUrl):
                    tg_name = extract_telegram_url(entity.url)

                    if (tg_name in tg_names) or (tg_name == 'None'):
                        continue
                        
                    tg_names.append(tg_name)

                    url = f'https://t.me/{tg_name}/'

                    try:
                        check_chat = await client.get_entity(url)
                        bar.next()
                        if check_chat.join_request:
                            tg_names.append(tg_name)
                            continue
                        else:
                            urls.append(url)
                    except FloodWaitError:
                        print("\nЛимит проверок исчерпан.")
                        bar.finish()
                        save_links(urls)
                        return
                    except Exception:
                        continue

            await client(GetBotCallbackAnswerRequest(
                            chat,
                            message.id,
                            data=message.reply_markup.rows[-1].buttons[-1].data
                        ))
            current_page += 1
        
        bar.finish()
        await client.disconnect()
    
    save_links(urls)

# ===================================================================================================================== #

def save_links(urls):
    links = '\n'.join(urls)
    with open(links_file_path, 'w') as f:
        f.write(links)
    print(f"Собранные ссылки сохранены в \"{links_file_path}\"")


def get_pages(message):
    match = re.search(r'Страница (\d+)/(\d+)', message)
    if match:
        current_page, total_pages = map(int, match.groups())
        return current_page, total_pages


def extract_telegram_url(url):
    pattern = r"t\.me/([^/]+)/"
    match = re.search(pattern, url)
    if match:
        return match.group(1)


async def get_message(client: TelegramClient, chat):
    messages = await client.get_messages(chat, None)
    message = messages[0]
    return message


def get_config():
    with open(config_file_path) as f:
        file_content = f.read()
        config = json.loads(file_content)
    return config

# ===================================================================================================================== #

if __name__ == "__main__":
    asyncio.run(main())
