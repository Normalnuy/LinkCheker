import os, json, asyncio, re, sys
from telethon import TelegramClient
from telethon.tl.types import MessageEntityTextUrl
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from progress.bar import Bar

script_dir = os.path.dirname(sys.argv[0])
config_file_path = os.path.join(script_dir, 'config.json')
session_file_path = os.path.join(script_dir, 'session\\client.session')
links_file_path = os.path.join(script_dir, 'result\\result.txt')

search_bot = "en_SearchBot"

async def main():

    try:

        os.system('cls||clear')
        if not os.path.exists(session_file_path):
            
            print("https://my.telegram.org/apps")
            api_id = input("API ID: ")
            api_hash = input("API Hash: ")
            to_config = {'api_id': api_id, 'api_hash': api_hash}
            
            print("Сохранение настроек...")
            with open(config_file_path, 'w') as f:
                f.write(json.dumps(to_config))
            print("Сохранение настроек: Успешно!")
            
            session = False
            while not session:
                print("Создание .session файла...")
                session = await create_session(api_id, api_hash)

        await parsing(search_bot)
    
    except Exception as e:
        print(f"Ошибка: {e}\nУдалите {session_file_path} файл и перезапустите программу.")
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

async def parsing(search_bot):
    
    input("Убедитесь, что вписали запрос в боте. Если это так - нажмите [Enter]: ")

    with open(config_file_path) as f:
        file_content = f.read()
        config = json.loads(file_content)
    
    api_id = config['api_id']
    api_hash = config['api_hash']
    
    async with TelegramClient(session_file_path, api_id=int(api_id), api_hash=api_hash) as client:

        chat = await client.get_entity(search_bot)

        message = await get_message(client, chat)
        await client(GetBotCallbackAnswerRequest(
                chat,
                message.id,
                data=message.reply_markup.rows[1].buttons[4].data
            ))
        message = await get_message(client, chat)

        pages = get_pages(message.message)

        current_page = pages[0]
        total_pages = pages[1]

        urls = []
        tg_names = []

        bar = Bar("Собираем ссылки по страницам...", max=total_pages)
        bar.next()

        for current_page in range(1, total_pages):

            for entity in message.entities:
                if isinstance(entity, MessageEntityTextUrl):
                    tg_name = extract_telegram_url(entity.url)

                    if tg_name not in tg_names and tg_name != 'None':
                        
                        url = f'https://t.me/{tg_name}/'
                        check_chat = await client.get_entity(url)
                        if check_chat.join_request:
                            break

                        tg_names.append(tg_name)
                        urls.append(url)

            await client(GetBotCallbackAnswerRequest(
                chat,
                message.id,
                data=message.reply_markup.rows[-1].buttons[-1].data
            ))
            message = await get_message(client, chat)

            current_page += 1
            bar.next()
        
        await client.disconnect()
        bar.finish()

    
    links = '\n'.join(urls)
    with open(links_file_path, 'w') as f:
        f.write(links)

    print(f"Собранные ссылки сохранены в \"{links_file_path}\"")

    # Закрываем?
    print("Нажмите [Ctrl + C] для завершения.")
    while True:
        pass

# ===================================================================================================================== #

def get_pages(message):
    match = re.search(r'Страница (\d+)/(\d+)', message)
    if match:
        current_page, total_pages = map(int, match.groups())
        return current_page, total_pages
    else:
        return None, None


def extract_telegram_url(url):
    pattern = r"t\.me/([^/]+)/"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None


async def get_message(client: TelegramClient, chat):
    messages = await client.get_messages(chat, None)
    message = messages[0]
    return message

# ===================================================================================================================== #

if __name__ == "__main__":
    asyncio.run(main())
