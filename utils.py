import random
from pprint import pprint


def str_to_dict(data):
    return dict(item.split(':') for item in data.replace('{','').replace('}','').replace('"','').split(','))


def get_random():
    return random.randint(0, 100000)

def send_error_msg(user_id,api, command='/start'):
    api.messages.send(user_id, message='Произошла ошибка пришлите комманду {}'.format(command),
                      random_id=get_random())

def keyboard_message(user_id ,api):
    api.messages.send(user_id=user_id, message='Воспользуйтесь клавиатурой', random_id=get_random())


def add_pagination_button(keyboard, page , num_page, f, pk=None, vk_id=None ):
    pages = []
    page = int(page)
    keyboard.add_line()

    n = 5
    if page > 1:

        if num_page - page < 2 and page > 3:
            counter = 3
            while counter > 0:
                pages.append(page-counter)
                counter -= 1
            n = 2
        else:
            pages.append(page-1)
            n = 4
    for i in range(1, n):
        if page + i <= num_page:
            pages.append(page+i)
    for p in pages:
        if pk:
            keyboard.add_button('Стр {}'.format(p), payload={'f':f,'page': p,'pk': pk})
        elif vk_id:
            keyboard.add_button('Стр {}'.format(p), payload={'f': f, 'page': p, 'pk': vk_id})
        else:
            keyboard.add_button('Стр {}'.format(p), payload={'f':f,'page': p})

    return keyboard

def get_lat_lon_point(group_id, message_id, api):
    data = api.messages.getById(message_ids=message_id, group_id=group_id)
    data = data['items'][0]
    if 'geo' in data:
        coord = data['geo']['coordinates']
        return ( coord['latitude'] ,coord['longitude'])


def ordersend_out_text(order):
    text = ('Ваш заказ\n\n')
    products_text = ''
    products = order['products'].split('%&')
    for product in products:
        items = product.split('@#')
        products_text = '{}{}\nколичество: {} шт\nНа сумму: {} руб\n\n'.format(products_text, items[1], items[2], items[3])

    text = '{}{}Доставка по адресу:\n{}\n'.format(text, products_text, order['adres'].split('%&')[0] )
    text = '{}Тел: {}\n\nНа сумму: {} руб'.format(text, order['phone'], order['total_summ'])
    pprint(order)
    return text
