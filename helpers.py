import logging


def get_title_selector(rules, domain):
    if 'title_tag' in rules:
        return rules['title_tag'], None

    elif 'title' in rules:
        return rules['title']['tag'], rules['title'].get('class')

    else:
        logging.warning('No title selector defined for {domain}, skipping...')

        return None, None