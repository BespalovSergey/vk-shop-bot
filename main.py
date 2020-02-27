import vk_bot


def main():
    try:
        bot = vk_bot.VkBot()
        bot.run_bot()
    except ConnectionError:
        print('Eroor BotSop')


if __name__ == "__main__":
    main()
