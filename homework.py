import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.info('Начало отправки')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.TelegramError as error:
        raise Exception(f'Не удалось отправить сообщение {error}')
    else:
        logging.debug(f'Сообщение отправлено {message}')


def get_api_answer(current_timestamp):
    """Получить статус домашней работы."""
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': current_timestamp},
    }
    try:
        logging.info(
            'Начало запроса: url = {url},'
            'headers = {headers},'
            'params = {params}'.format(**params_request))
        homework_statuses = requests.get(**params_request)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise exceptions.InvalidResponseCode(
                'Не удалось получить ответ API, '
                f'ошибка: {homework_statuses.status_code}'
                f'причина: {homework_statuses.reason}'
                f'текст: {homework_statuses.text}')
        try:
            return homework_statuses.json()
        except ValueError as e:
            raise exceptions.InvalidResponseFormat(
                'Ошибка декодирования ответа API: {error}. '
                'Полученный ответ: {response}'.format(
                    error=str(e),
                    response=homework_statuses.text))
    except requests.RequestException as e:
        raise exceptions.ConnectingError(
            'Не верный код ответа параметры запроса: url = {url},'
            'headers = {headers},'
            'params = {params}'.format(**params_request)) from e


def parse_status(homework):
    """Распарсить ответ."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутсвует ключ homework_name')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    return (
        'Изменился статус проверки работы "{homework_name}" {verdict}'
    ).format(
        homework_name=homework_name,
        verdict=HOMEWORK_VERDICTS[homework_status]
    )


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.info('Проверка ответа от API')
    if not isinstance(response, dict):
        raise TypeError('Ответ API должен быть словарем')
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homeworks" в ответе API')
    if 'current_date' not in response:
        logging.error('Отсутствует ключ "current_date" в ответе API')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Значение ключа "homeworks" должно быть списком')
    return homeworks


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует необходимое кол-во'
                         ' переменных окружения')
        sys.exit('Отсутствуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_report = {
        'name': '',
        'output': ''
    }
    prev_report = current_report.copy()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            new_homeworks = check_response(response)
            current_timestamp = response.get(
                'current_data', current_timestamp)
            if new_homeworks:
                homework = new_homeworks[0]
                homework_status = homework.get('status')
                if homework_status in HOMEWORK_VERDICTS:
                    homework_verdict = HOMEWORK_VERDICTS[homework_status]
                    current_report['output'] = homework_verdict
                else:
                    current_report['output'] = homework_status
            else:
                current_report['output'] = 'Нет новых статусов работ.'
            if current_report != prev_report:
                send = f' {current_report["name"]}, {current_report["output"]}'
                send_message(bot, send)
                prev_report = current_report.copy()
            else:
                logging.debug('Статус не поменялся')
        except exceptions.NotForSending as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['output'] = message
            logging.error(message)
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy
        finally:
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        filename='homework.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    main()
