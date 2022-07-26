import logging
import os
import requests
import sys
import time

from telegram import Bot
from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('YP_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = '358030006'

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info('начали отправку сообщения в Telegram')
    if not bot.send_message(TELEGRAM_CHAT_ID, message):
        raise Exception('сбой при отправке сообщения в Telegram ')
    logging.info(f'сообщение удачно отправлено: {message}')


def get_api_answer(current_timestamp):
    """делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, params, headers=HEADERS,)
    if response.status_code != HTTPStatus.OK:
        raise Exception(logging.error('ошибка: API недоступен'))
    logging.info('начали запрос к API')
    return response.json()


def check_response(response):
    """проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(('response возвращает неверный тип данных'))
    if 'homeworks' not in response.keys():
        raise KeyError(('ответ от API не содержит ключа homeworks'))
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('домашки приходят не в виде списка в ответ от API')
    return response.get('homeworks')


def parse_status(homework):
    """извлекает из информации о конкретной домашней работе.

    статус этой работы.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(('неправильный статус домашней работы'))
    if 'homework_name' not in homework.keys():
        raise KeyError(('отсутствует ключ homework_name в ответе от API'))
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            if not check_tokens():
                sys.exit('отсутствие обязательных переменных окружения')
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            get_api_answer(current_timestamp)
            if homework:
                send_message(bot, parse_status(homework[0]))
                current_timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
