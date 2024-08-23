producer_config = {
    'bootstrap.servers': '',
} #продюсер Кафка

consumer_config = {
    'bootstrap.servers': '',
    'group.id': 'mygroup',
    'auto.offset.reset': 'earliest'
} # консьюмер Кафка

webdriver_path = './venv/bin/chromedriver' #путь до вебдрайвера

twitter_username = '' #логин твиттер
twitter_password = '' #пароль твиттер

discord_username = '' #логин дискорд
discord_password = '' #пароль дискорд
discord_server = '' #сервер дискорд
list_roles = [] #список ролей на сервере

following_twitter = 'validate-twitter-subscription' #топик для запроса проверки подписки на твиттер
following_discord = 'validate-discord-subscription' #топик для запроса проверки наличия на сервере дискорд
confirm_subscription = 'confirm-subscription' #топик для ответа подписки на твиттер и наличия на сервере дискорд
post_twitter = 'twitter-account-check' #топик для запроса наличия у пользователя поста
twit_status = 'twitter-tweet-status' #топик для ответа наличия у пользователя поста
role_user_discord = 'discord_input_topic' #топик для запроса ролей у пользоваетля в дискорде
role_discord = 'discord_output_topic' #топик для ответа на запрос ролей у пользователя
