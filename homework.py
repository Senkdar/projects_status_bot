import logging
import os
import requests
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
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'сообщение удачно отправлено: {message}')
    except Exception:
        logging.error('сбой при отправке сообщения в Telegram ')


def get_api_answer(current_timestamp):
    """делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, params, headers=HEADERS,)
    if response.status_code != HTTPStatus.OK:
        raise Exception(logging.error('ошибка: API недоступен'))
    return response.json()


def check_response(response):
    """проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(
            logging.error('response возвращает неверный тип данных')
        )
    if 'homeworks' not in response.keys():
        raise KeyError(
            logging.error('ответ от API не содержит ключа homeworks')
        )
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('домашки приходят не в виде списка в ответ от API')
    return response.get('homeworks')


def parse_status(homework):
    """извлекает из информации о конкретной домашней работе.

    статус этой работы.
    """
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(
            logging.error('неправильный статус домашней работы')
        )
    if 'homework_name' not in homework.keys():
        raise KeyError(
            logging.error('отсутствует ключ homework_name в ответе от API')
        )
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """проверяет доступность переменных окружения."""
    *variables, = PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    if all(variables):
        return True
    else:
        logging.critical('отсутствие обязательных переменных окружения')
        return False


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            if not check_tokens():
                break
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            get_api_answer(current_timestamp)
            if homework:
                send_message(bot, parse_status(homework[0]))
                current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()
