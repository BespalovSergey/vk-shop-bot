from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardButton,VkKeyboardColor
import vk_api
import random
import pprint
from state_base import DB
import requests
import json
from utils import str_to_dict, get_random, send_error_msg, keyboard_message,\
                  add_pagination_button, get_lat_lon_point, ordersend_out_text



class VkBot():

    def __init__(self):
        self.shop_token = 'Токен Магазина'
        self.vk_token = 'Токен для группы вконтакте'
        self.database = DB()
        self.headers = {'Authorization': 'Token {}'.format(self.shop_token)}
        self.domain = 'http://127.0.0.1:8000'
        self.group_id = 'Id группы бота вконтакте '
        self.yandex_api = 'Api key яндекс карт'



    def get_key_board(self, type=None, data=None, all_cat = False, location = False, event=None, **kwargs):

        keyboard = VkKeyboard()
        if type == 'categorys':
            for i, item in enumerate(data):
                keyboard.add_button(item['name'], payload={'pk':item['id']})
                if  i % 2  and i != len(data)-1:
                    keyboard.add_line()
            if kwargs['num_page'] > 1:
                keyboard = add_pagination_button(keyboard, kwargs['page'], kwargs['num_page'], 'ST')

        if type == 'products':
            cat_id = data[0]['category']['id']
            for i, item in enumerate(data):
                keyboard.add_button(item['name'], payload={'pk':item['id']})
                if i % 2 and i != len(data) - 1:
                    keyboard.add_line()
            if kwargs['num_page'] > 1:
                keyboard = add_pagination_button(keyboard, kwargs['page'], kwargs['num_page'], 'CP', cat_id)

        if 'add_to_cart' in kwargs:
            id = kwargs['add_to_cart']
            keyboard.add_button('Добавить корзину', color='positive', payload={'f':'ATC','pk':id})
        if 'view_cart' in kwargs:
            cart_id = str(kwargs['view_cart'])
            if len(keyboard.lines)>0:
                keyboard.add_line()
            keyboard.add_button('Корзина', color='primary', payload={'f':'VC','c_id':cart_id})
        if all_cat:
            if len(keyboard.lines[-1])>0:
                keyboard.add_line()
            keyboard.add_button('Все категории', payload={'f':'ST'})
        if 'cat' in kwargs:
            category = kwargs['cat']
            keyboard.add_button(category['name'], payload={'f':'CP','pk':category['id']})
        if 'create_order' in kwargs and kwargs['create_order']:
            keyboard.add_line()
            keyboard.add_button('Оформить заказ', color='positive', payload={'f':'SA','pk':kwargs['create_order']['id']})
        if 'delete_from_cart' in kwargs:
            cart_items = kwargs['delete_from_cart']
            if len(cart_items)>0:
                if len(keyboard.lines[-1]) > 0 :
                    keyboard.add_line()

                for i,item in enumerate(cart_items):
                    keyboard.add_button(item['product']['name'], payload={'f': 'PD', 'pk': item['product']['id']})
                    keyboard.add_button('Удалить', color='negative', payload={'f':'DFC','pk':item['product']['id']})

                    if i < len(cart_items)-1:
                        keyboard.add_line()
                if kwargs['num_page'] > 1:
                    keyboard = add_pagination_button(keyboard, kwargs['page'], kwargs['num_page'], 'VC',
                                                     vk_id=kwargs['vk_id'])
        if 'adreses' in kwargs and kwargs['adreses']:
            adreses = kwargs['adreses']
            if len(keyboard.lines[-1]) > 0:
                keyboard.add_line()

            for i, adres in enumerate(adreses):
                keyboard.add_button('{}: {}'.format(i+1,adres['adres']),payload={'f':'SP','pk':adres['id']})
                keyboard.add_button('Удалить', color='negative', payload={'f':'DA','pk':adres['id']})
                if i < len(adreses)-1:
                    keyboard.add_line()

        if 'phone' in kwargs and kwargs['phone']:
            keyboard.add_line()
            keyboard.add_button('Подтвердить: {}'.format(kwargs['phone']), payload={'f':'WP','p':kwargs['phone']})
        if location:
            keyboard.add_line()
            keyboard.add_location_button(payload={'f':'SP'})

        return keyboard.get_keyboard()


    def handle_user_reply(self,event, api):
        event_data = {}
        if hasattr( event,'payload'):
            event_data = str_to_dict(event.payload)
            user_reply = event.payload
            user_id= event.user_id
            user_key = 'user_{}'.format(user_id)
        elif event.text:
            user_reply = event.text
            user_id = event.user_id
            user_key = 'user_{}'.format(user_id)
        else:
            return

        if user_reply == '/start':
            user_state = 'ST'
        else:
            if 'f' in event_data:
                user_state = event_data['f']
            else:
                user_state = self.database.get_value(user_key)

        print('user_state   ',   user_state)
        state_functions ={
            'ST': self.start,
            'CP': self.category_product,
            'PD': self.product_detail,
            'ATC': self.add_to_cart,
            'DFC': self.delete_from_cart,
            'VC': self.view_cart,
            'SA': self.set_adres,
            'SP': self.set_phone,
            'DA': self.delete_adres,
            'WP': self.write_phone,
            'OS': self.order_send,
        }
        if not user_state:
            api.messages.send(user_id=user_id, message='Пришлите комманду /start', random_id= random.randint(1,10000))
            return
        state_handler = state_functions[user_state]
        next_state = state_handler(event,api)
        print(next_state)
        self.database.set_value(user_key, next_state)

    def start(self,event, api):
        params = {}
        url = '{}/api/categorys'.format(self.domain)
        if hasattr(event, 'payload'):
            event_data = str_to_dict(event.payload)
            if 'page' in event_data:
                params['page'] = event_data['page']
        response = requests.get(url=url, params= params,  headers=self.headers)
        if response.status_code == requests.codes.ok:
            response = response.json()
            categorys = response['categorys']
            page = response['page']
            num_page = response['num_page']
            message_text = 'Выберете категорю товара'
            if response['num_page'] > 1:
                message_text = '{}\n\nСтраница {} из {}'.format(message_text, page, num_page)

            api.messages.send(user_id=event.user_id, message=message_text,
                              keyboard = self.get_key_board('categorys',categorys,view_cart=event.user_id,
                                                            page= page, num_page=num_page), random_id= get_random())
        else:
            return 'ST'
        return 'CP'
    def product_detail(self,event, api):
        if hasattr(event, 'payload'):
            url = '{}/api/product_detail'.format(self.domain)
            event_data = str_to_dict(event.payload)
            data={}
            data['pk'] = event_data['pk']
            data['v_id'] = event.user_id
            response = requests.get(url=url, params=data, headers=self.headers)
            if response.status_code == requests.codes.ok:
                response = response.json()
                prod = response['product']
                cart_item = response['cart_item']
                message_text = '{}\nЦена: {} руб'.format(prod['name'],prod['price'])
                if prod['description']:
                    message_text = '{}\n\n{}'.format(message_text,prod['description'])
                if cart_item:
                    message_text = '{}\n\nBкорзине {} шт\nНа сумму {} руб'.format(message_text, cart_item['qty'],cart_item['item_total'])
                else:
                    message_text = '{}\n\nНет в корзине'.format(message_text)
                attach=[]
                for image in prod['images'] :
                    if 'http' in image['file_url']:
                        link = image['image_link'][image['image_link'].rfind('z=')+2:]
                        attach.append(link)

                api.messages.send(user_id=event.user_id, message=message_text, random_id=get_random(),attachment=attach,
                                  keyboard=self.get_key_board(all_cat=True, cat=prod['category'], add_to_cart=prod['id'],
                                                              view_cart=event.user_id))
            else:
                return 'PD'
        else:
            keyboard_message(event.user_id,api)
            return'PD'
        return 'PD'

    def view_cart(self,event,api):
        if hasattr(event, 'payload'):
            url = '{}/api/get_cart'.format(self.domain)
            event_data = str_to_dict(event.payload)
            if 'c_id' in event_data:
                params={'cart_id': event_data['c_id']}
            else: params = {'cart_id': event.user_id}
            if 'page' in event_data:
                params['page'] = event_data['page']
            response = requests.get(url=url, params=params, headers=self.headers)
            if response.status_code == requests.codes.ok:
                response = response.json()
                cart = response['cart']
                cart_items = response['cart_items']
                message_text = 'Ваша корзина'
                create_order = cart
                if len(cart['items']):
                    for i, item in enumerate(cart['items']):
                        text = '\n{}.  {}:\n  Вкорзине {}шт на {}руб\n'.format(i+1,item['product']['name'], item['qty'],
                                                                         item['item_total'])
                        message_text = '{}{}'.format(message_text,text)
                    message_text = '{}\n\nНа сумму: {}руб'.format(message_text, cart['cart_total'])
                    if response['num_page'] > 1:
                        message_text = '{}\n\nНа клавиатуре , часть товаров\nСтраница {} из {}'.format(message_text, response['page'],
                                                                        response['num_page'])
                else:
                    message_text = 'Ваша корзина пуста'
                    create_order = False
                api.messages.send(user_id=event.user_id, message=message_text, random_id=get_random(),
                                  keyboard=self.get_key_board(all_cat=True, delete_from_cart=cart_items,
                                                              page=response['page'], num_page=response['num_page'],
                                                              vk_id=event.user_id , create_order= create_order))
        else:
            keyboard_message(event.user_id,api)

    def delete_from_cart(self,event, api):
        if hasattr(event, 'payload'):
            url = '{}/api/remove_from_cart'.format(self.domain)
            event_data = str_to_dict(event.payload)
            data ={'ppk': event_data['pk'],
                   'vk_id': str(event.user_id)}
            response = requests.post(url,data,headers=self.headers)
            if response.status_code == requests.codes.ok:
                if response.json()['result'] == 'OK':
                    self.view_cart(event, api)
        else:
            return 'DFC'

    def add_to_cart(self, event, api):
        try:
            event_data = str_to_dict(event.payload)
        except:
            send_error_msg(event.user_id, api)
            return 'ST'
        url = '{}/api/add_to_cart'.format(self.domain)
        params = {'user_id': event.user_id,
                  'pk': event_data['pk']}
        response = requests.post(url=url, data=params, headers=self.headers)
        if response.status_code == requests.codes.ok:

            self.product_detail(event, api)
        else:
            return 'ST'




    def category_product(self,event, api):
        if hasattr(event,'payload'):
            data = str_to_dict(event.payload)
            url = '{}/api/products'.format(self.domain)
            response = requests.get(url=url, params=data, headers=self.headers)

            if response.status_code == requests.codes.ok:
                response = response.json()
                page = response['page']
                num_page = response['num_page']
                category = response['products'][0]['category']
                message_text = 'Товары категории {}'.format(category['name'])

                if response['num_page'] > 1:
                    message_text = '{}\n\nСтраница {} из {}'.format(message_text, page,num_page)
                api.messages.send(user_id=event.user_id, message= message_text,
                                  keyboard=self.get_key_board(type='products', data=response['products'], event=event,
                                                              all_cat=True, page=page, num_page=num_page,view_cart=event.user_id), random_id=get_random())
                return 'PD'
            else:
                return 'CP'
        else:
            keyboard_message(event.user_id,api)
            return 'CP'

    def set_adres(self, event, api):
        if hasattr(event, 'payload'):
            event_data = str_to_dict(event.payload)
            url = '{}/api/user_adreses'.format(self.domain)
            user = api.users.get(user_ids=event.user_id, fields=['domain', 'photo'])[0]
            data = {'vk_id': event.user_id,
                    'first_name': user['first_name'], 'last_name': user['last_name'],
                    'photo': user['photo'], 'domain': user['domain']}
            response = requests.post(url, data, headers=self.headers)
            if response.status_code == requests.codes.ok:
                message_text = 'Пришлите адрес доставки\n'
                vk_user = response.json()['vk_user']
                adreses = None
                if len(vk_user['adreses']):
                    adreses = vk_user['adreses']
                    message_text = '{}Или выберете из списка\n\n'.format(message_text)
                    adreses_text = ''
                    for i, adres in enumerate(adreses):
                        adreses_text = '{}{}: {}\n\n'.format(adreses_text, i+1, adres['adres'])
                    message_text = '{}{}'.format(message_text, adreses_text)

                api.messages.send(user_id=event.user_id, message=message_text,
                                  keyboard=self.get_key_board(all_cat=True, adreses=adreses),
                                  random_id=get_random())
                return 'SP'
        else:
            keyboard_message(event.user_id, api)

    def  delete_adres(self, event, api):
        adres = None
        if hasattr(event, 'payload'):
            url = '{}/api/remove_user_adres'.format(self.domain)
            event_data = str_to_dict(event.payload)
            data = {'pk':event_data['pk']}
            response = requests.post(url, data, headers=self.headers)
            return self.set_adres(event, api)
        else:
            keyboard_message(event.user_id, api)

    def set_phone(self, event, api):
        if hasattr(event, 'payload'):
            event_data= str_to_dict(event.payload)
            adres = event_data['pk']
        else:
            url = '{}/api/add_user_adres'.format(self.domain)
            data={'vk_id':event.user_id,
                  'adres':event.text}
            response = requests.post(url, data, headers=self.headers)
            if response.status_code == requests.codes.ok:
                adres = response.json()['adres']
        if adres:
            url = '{}/api/add_order_adres'.format(self.domain)
            data = {'pk':adres,
                    'vk_id':event.user_id}
            response = requests.post(url, data, headers=self.headers)
            if response.status_code == requests.codes.ok:
                order = response.json()['order']
                phone = order['user']['phone']
                message_text = 'Пришлите номер телефона для связи'
                if phone:
                    message_text = 'Подтвердите указанный телефон\n{}\nИли пришлите другой номер'.format(phone)
                api.messages.send(user_id=event.user_id, message=message_text,
                                  keyboard= self.get_key_board(all_cat=True, phone= phone),
                                  random_id=get_random())

        return 'WP'

    def write_phone(self, event, api):
        if hasattr(event, 'payload'):
            phone= str_to_dict(event.payload)['p']
        else:
            phone = event.text
        url = '{}/api/add_order_phone'.format(self.domain)
        data = {'vk_id': event.user_id,
                'phone': phone}
        response = requests.post(url, data, headers= self.headers)
        if response.status_code == requests.codes.ok:
            order = response.json()['order']
            api.messages.send(user_id=event.user_id, message=ordersend_out_text(order), random_id=get_random())
        event.payload = "{'f':'SA'}"
        return self.set_adres(event, api)


    def order_send(self, event, api):
        pass


    def run_bot(self):
        vk_session = vk_api.VkApi(token=self.vk_token)
        api = vk_session.get_api()
        longpooll = VkLongPoll(vk_session)

        for event in longpooll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.handle_user_reply(event, api)






