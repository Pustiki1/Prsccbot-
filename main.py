from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from db_for_promo import Promocode, init_db
from datetime import datetime
import logging
import random
import os
import csv

init_db()
BOT_TOKEN = "8667812775:AAEEf8mXqj6bUQzAQRwwLlNtOhbGeoMxcOg"
MODERATIONS = ["@pustiki1"]
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
EMAIL, PHONE, FIO, CONFIRM, PROMO = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.name in MODERATIONS:
        logger.info(f"Модератор {update.effective_user.name} запустил команду /start")
        await update.message.reply_text('Вы вошли под аккаунтом модератора, вам доступны функции админа: /create_promo https://disk.yandex.ru/d/_6MRriJo4iQekA')
    elif update.effective_user.name is None:
        await update.message.reply_text('Для пользования этим ботом нужно сделать свой tg-id видимым!')
    else:
        logger.info(f"Пользователь {update.effective_user.name} запустил команду /start")
        await update.message.reply_text(
            'Йоу! Это telegram-бот Prosecco Show, твой проводник в мир импрова.\nСпасибо за то, что проявил интерес к команде и решил присоединиться к нашему сообществу.\nСпециально для тебя мы подготовили два подарка - 📚методичку импровизатора📚 и целый месяц бесплатной подписки на наш 🌟закрытый канал🌟!\nЧтобы забрать оба подарка мы предлагаем познакомиться, для этого пройди регистрацию, ответив всего на пару вопросов.\nДля начала регистрации используй команду /register \nНаша политика использования персональных данных: https://disk.yandex.ru/d/_6MRriJo4iQekA')


async def helpper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.name is None:
        await update.message.reply_text('Для пользования этим ботом нужно сделать свой tg-id видимым!')
    elif update.effective_user.name in MODERATIONS:
        logger.info(f"Модератор {update.effective_user.name} запустил команду /help")
        await update.message.reply_text(
            'Вот какими командами вы можете воспользоваться:\n/start - start\n'
            '/help - помощь\n/register - регистрация\n/create_promo - создать новый промокод')
    else:
        logger.info(f"Пользователь {update.effective_user.name} запустил команду /help")
        await update.message.reply_text(
            'Вот какими командами вы можете воспользоваться:\n/start - start\n/help - помощь\n/register - регистрация ')


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.name is None:
        await update.message.reply_text('Для пользования этим ботом нужно сделать свой tg-id видимым!')
        return ConversationHandler.END

    else:
        logger.info(f"Пользователь {update.effective_user.name} запустил команду /register")
        await update.message.reply_text("Введи имя и фамилию:")
        return FIO


async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fio = update.message.text
    context.user_data['fio'] = fio
    context.user_data['tg_username'] = update.effective_user.name
    await update.message.reply_text("Введи номер телефона:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['phone'] = phone
    await update.message.reply_text("Введи электронную почту:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if '@' not in email or '.' not in email:
        await update.message.reply_text("❌ Неверный формат почты. Попробуй снова:")
        return EMAIL

    context.user_data['email'] = email
    fio = context.user_data['fio']
    phone = context.user_data['phone']
    tg_username = context.user_data['tg_username']

    await update.message.reply_text(
        f"Проверьте данные:\n"
        f"Username: {tg_username}\n"
        f"Email: {email}\n"
        f"Телефон: {phone}\n"
        f"Имя: {fio}\n\n"
        f"Всё верно? (да/нет - словом)"
    )

    return CONFIRM


async def confirm_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.lower()

    if answer == 'да':
        await update.message.reply_text("Отлично, теперь самое важное, введи свой промокод:")
        return PROMO
    else:
        await update.message.reply_text("Начнём заново! Введи почту:")
        return FIO


async def get_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    promo = update.message.text
    request = Promocode.check_promo(promo)
    if request == "success":
        await update.message.reply_text("Отлично, промокод верный!")
        logger.info(f"Тут должна быть регистрация о пользователе: {context.user_data['tg_username']}, "
                    f"{context.user_data['email']}, "
                    f"{context.user_data['phone']}"
                    f", {context.user_data['fio']}")

        response = await register_user_in_db(context.user_data['tg_username'], context.user_data['email'],
                                             context.user_data['phone'], context.user_data['fio'])
        if response == "success":
            # Здесь можно сохранить данные или продолжить регистрацию
            await update.message.reply_text(
                f"✅ Регистрация завершена!\nФИО: {context.user_data['fio']}\nТелефон: {context.user_data['phone']}\nEmail: {context.user_data['email']} сохранены, спасибо! \n🌟Твоя ссылка на канал: https://t.me/+kIz5X1BdFXo2N2Zi🌟 \n 📚Методичку найдешь там в закрепе!📚 \nОчень рады тебе!")

        else:
            logger.info(response)
            await update.message.reply_text("Произошла ошибка! Попробуйте позже")


    elif request == "error":
        await update.message.reply_text("Промокод не верный, проверьте его правильность и введите еще раз:")
        return PROMO
    else:
        await update.message.reply_text("Произошла ошибка, приносим извинения, попробуйте позже!")


async def register_user_in_db(username, email, phone, fio):
    file_exists = os.path.isfile('contacts.csv')
    try:
        with open('contacts.csv', 'a', newline='', encoding='UTF-8') as csvfile:
            fieldnames = ['timestamp', 'telegram_id', 'full_name', 'phone', 'email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'telegram_id': username,
                'full_name': fio,
                'phone': phone,
                'email': email
            })
        return "success"
    except Exception as e:
        return str(e)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Регистрация отменена")
    return ConversationHandler.END


async def create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.name in MODERATIONS:
        promocode = await generate_clear_promocode()
        logger.info(
            f"Модератор {update.effective_user.name} запустил команду /create_promo, получил промокод: {promocode}")
        add_new_promo = Promocode.add_new_promocode(promocode)
        if add_new_promo == "success":
            logger.info(f"Модератор {update.effective_user.name} успешно добавил промо {promocode} в бд")
            await update.message.reply_text(promocode)
        else:
            logger.info(f"Произошла ошибка: {add_new_promo}")
            await update.message.reply_text("Произошла ошибка, попробуйте позже")
    else:
        logger.info(
            f"Пользователь {update.effective_user.name} запустил команду /create_promo и у него на это не было прав")
        await update.message.reply_text('Это команда только для модераторов!')


async def generate_clear_promocode(length=16):
    safe_chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    promocode = ''.join(random.choice(safe_chars) for _ in range(length))
    return promocode


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 2. Регистрируем обработчики (handlers)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_promo", create_promo))
    app.add_handler(CommandHandler("help", helpper))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register)],
        states={
            FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PROMO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_promo)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_data)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    # 3. Запускаем бота
    app.run_polling()


if __name__ == '__main__':
    main()
