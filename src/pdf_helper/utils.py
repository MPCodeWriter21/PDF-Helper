import re

POSITION_PATTERN = re.compile(
    r'^(top|bottom|center|left|right|\d{1,3}%?)\s+(top|bottom|center|left|right|\d{1,3}%?)?$'
)


def parse_pages(pages: str) -> list[int]:
    """Parses the pages string into a list of pages.

    :param pages: The pages string
        Example: '1-5,7,9-11'
    :return: A list of pages
        Example: [1, 2, 3, 4, 5, 7, 9, 10, 11]
    """
    pages_ = pages.replace(' ', '')
    pages_ = pages_.split(',')
    pages_ = [x.split('-') for x in pages_]
    pages_ = [x if len(x) == 1 else range(int(x[0]), int(x[1]) + 1) for x in pages_]
    pages_ = [int(x) for y in pages_ for x in y]
    return pages_


def parse_position(
    position: str, page_width: float, page_height: float, text_width: float,
    text_height: float
) -> tuple[float, float]:
    """Parse position string into x and y coordinates.

    :param position: Position string.
    :param page_width: Width of the page.
    :param page_height: Height of the page.
    :param text_width: Width of the text.
    :param text_height: Height of the text.
    :return: x and y coordinates.
    """
    position = position.lower().strip()
    match = POSITION_PATTERN.match(position)
    if not match:
        raise ValueError(f'Invalid position string: {position}')

    groups = match.groups()
    if len(groups) == 1:
        value = groups[0]
        if value == 'center':
            return (page_width - text_width) / 2, (page_height - text_height) / 2
        elif value == 'top':
            return (page_width - text_width) / 2, 0
        elif value == 'bottom':
            return (page_width - text_width) / 2, page_height - text_height
        elif value == 'left':
            return 0, (page_height - text_height) / 2
        elif value == 'right':
            return page_width - text_width, (page_height - text_height) / 2
        elif value.endswith('%'):
            percent = float(value[:-1]) / 100.0
            return (page_width -
                    text_width) * percent, (page_height - text_height) * percent
        else:
            absolute = float(value)
            return absolute, absolute
    elif len(groups) == 2:
        x_value, y_value = groups
        if x_value == 'center':
            x = (page_width - text_width) / 2
        elif x_value == 'top' or x_value == 'bottom':
            raise ValueError(f'Invalid x position: {x_value}')
        elif x_value == 'left':
            x = 0
        elif x_value == 'right':
            x = page_width - text_width
        elif x_value.endswith('%'):
            percent = float(x_value[:-1]) / 100.0
            x = (page_width - text_width) * percent
        else:
            x = float(x_value)

        if y_value == 'center':
            y = (page_height - text_height) / 2
        elif y_value == 'left' or y_value == 'right':
            raise ValueError(f'Invalid y position: {y_value}')
        elif y_value == 'top':
            y = 0
        elif y_value == 'bottom':
            y = page_height - text_height
        elif y_value.endswith('%'):
            percent = float(y_value[:-1]) / 100.0
            y = (page_height - text_height) * percent
        else:
            y = float(y_value)

        return x, y
    else:
        raise ValueError(f'Invalid position string: {position}')
