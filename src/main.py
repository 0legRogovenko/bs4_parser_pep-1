import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import DOWNLOADS_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, get_soup

PARSER_STARTED_MSG = 'Парсер запущен!'
ARGS_MSG = 'Аргументы командной строки: {args}'
DOWNLOAD_SUCCESS_MSG = 'Архив был загружен и сохранён: {archive_path}'
MISMATCH_WARNING_MSG = 'Несовпадающие статусы:'
MISMATCH_DETAIL_MSG = (
    '\n%s \n'
    'Статус в карточке: %s \n'
    'Ожидаемые статусы: %s'
)
PARSER_DONE_MSG = 'Парсер завершил работу.'
VERSIONS_NOT_FOUND_MSG = 'Ничего не нашлось'


def whats_new(session):
    """Парсит страницу «What's New in Python» и возвращает список статей."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    try:
        soup = get_soup(session, whats_new_url)
    except ConnectionError as error:
        logging.warning(str(error))
        return results
    selector = '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 a'
    for a_tag in tqdm(soup.select(selector)):
        version_link = urljoin(whats_new_url, a_tag['href'])
        try:
            article_soup = get_soup(session, version_link)
        except ConnectionError as error:
            logging.warning(str(error))
            continue
        h1 = find_tag(article_soup, 'h1')
        dl = find_tag(article_soup, 'dl')
        results.append((version_link, h1.text, dl.text))
    return results


def latest_versions(session):
    """
    Парсит список версий Python с их статусами и ссылками на документацию.
    """
    soup = get_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException(VERSIONS_NOT_FOUND_MSG)
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((a_tag['href'], version, status))
    return results


def download(session):
    """Скачивает ZIP-архив с документацией Python в директорию downloads/."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session, downloads_url)
    main_tag = soup.find('div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+\.zip$')},
    )
    archive_url = urljoin(downloads_url, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOADS_DIR / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_SUCCESS_MSG.format(archive_path=archive_path))


def get_pep_status(session, url):
    """Загружает страницу PEP и возвращает значение поля Status."""
    soup = get_soup(session, url)
    status_dt = soup.find(
        lambda tag: tag.name == 'dt' and 'Status' in tag.text,
    )
    if status_dt is None:
        return None
    status_dd = status_dt.find_next_sibling('dd')
    if status_dd is None:
        return None
    return status_dd.text.strip()


def get_pep_rows(table):
    """Извлекает строки PEP из HTML-таблицы."""
    rows = []
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if not cols or len(cols[0].text.strip()) > 2:
            continue
        preview_status = cols[0].text.strip()[1:]
        expected_statuses = EXPECTED_STATUS.get(preview_status, [])
        pep_link_tag = cols[1].find('a')
        if pep_link_tag is None:
            continue
        if cols[1].text.strip() == '0':
            continue
        rows.append((
            urljoin(PEP_URL, pep_link_tag['href']),
            expected_statuses,
        ))
    return rows


def pep(session):
    """Парсит все документы PEP и возвращает количество PEP по статусам."""
    soup = get_soup(session, PEP_URL)
    status_count = defaultdict(int)
    mismatched = []
    all_rows = [
        row for table in soup.find_all('table')
        for row in get_pep_rows(table)
    ]
    for pep_link, expected in tqdm(all_rows):
        try:
            actual = get_pep_status(session, pep_link)
        except ConnectionError as error:
            logging.warning(str(error))
            continue
        if actual is None:
            continue
        if actual not in expected:
            mismatched.append((pep_link, actual, list(expected)))
        status_count[actual] += 1
    if mismatched:
        logging.warning(MISMATCH_WARNING_MSG)
        for url, actual, expected in mismatched:
            logging.warning(MISMATCH_DETAIL_MSG, url, actual, expected)
    return [
        ('Статус', 'Количество'),
        *status_count.items(),
        ('Всего', sum(status_count.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    """Точка входа: настраивает окружение и запускает выбранный парсер."""
    configure_logging()
    logging.info(PARSER_STARTED_MSG)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(ARGS_MSG.format(args=args))
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as error:
        logging.exception(error)
        return
    logging.info(PARSER_DONE_MSG)


if __name__ == '__main__':
    main()
