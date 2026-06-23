from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

CONNECTION_ERROR_MSG = 'Возникла ошибка при загрузке страницы {url}: {error}'
TAG_NOT_FOUND_MSG = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='utf-8'):
    """Выполняет GET-запрос и возвращает объект ответа."""
    try:
        response = session.get(url, timeout=3)
        response.encoding = encoding
        return response
    except RequestException as error:
        raise ConnectionError(
            CONNECTION_ERROR_MSG.format(url=url, error=error),
        ) from error


def get_soup(session, url, parser='lxml'):
    """Загружает страницу и возвращает объект BeautifulSoup."""
    return BeautifulSoup(get_response(session, url).text, parser)


def find_tag(soup, tag, attrs=None):
    """Ищет тег в объекте BeautifulSoup и возвращает его."""
    searched_tag = soup.find(tag, attrs=(attrs if attrs is not None else {}))
    if searched_tag is None:
        raise ParserFindTagException(
            TAG_NOT_FOUND_MSG.format(tag=tag, attrs=attrs),
        )
    return searched_tag
