import logging
import re
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, ContextTypes, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
from dotenv import load_dotenv
import time
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN, TWOCAPTCHA_API_KEY = os.getenv('8328628093:AAEfg9WELg4IRnHQpPJOQ7UNQi6sBWZXNlc'), os.getenv('b832ee80092b80010c8d7aef27bbf9aa')
EMAIL, = range(1)

def solve_captcha(driver, wait):
    if not TWOCAPTCHA_API_KEY:
        return False
    try:
        site_key = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'g-recaptcha'))).get_attribute('data-sitekey')
        page_url = driver.current_url
        r = requests.post('http://2captcha.com/in.php', data={'key': TWOCAPTCHA_API_KEY, 'method': 'userrecaptcha', 'googlekey': site_key, 'pageurl': page_url, 'json': 1})
        if r.json().get('status') == 1:
            time.sleep(15)
            r = requests.post('http://2captcha.com/res.php', data={'key': TWOCAPTCHA_API_KEY, 'action': 'get', 'id': r.json()['request'], 'json': 1})
            if r.json().get('status') == 1:
                captcha = r.json()['request']
                driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML = "{captcha}";')
                wait.until(EC.element_to_be_clickable((By.ID, 'continue'))).click()
                return True
    except Exception as e:
        logger.error(f'Error en CAPTCHA: {e}')
    return False

def generate_random_name():
    names = ['John', 'Mike', 'Sarah', 'Emma', 'Alex']
    return f"{random.choice(names)}{random.randint(100, 999)}"

def generate_random_password(length=12):
    """Genera una contraseña aleatoria segura."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Usa /crear_cuenta para crear cuenta automáticamente. ⚠️ Riesgo de violación de TOS.')

async def crear_cuenta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Ingresa tu correo electrónico.')
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    nombre = generate_random_name()
    password = generate_random_password()
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('user-agent=Mozilla/5.0')
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get('https://www.amazon.com/ap/register')
        wait.until(EC.presence_of_element_located((By.ID, 'ap_customer_name'))).send_keys(nombre)
        wait.until(EC.presence_of_element_located((By.ID, 'ap_email'))).send_keys(email)
        wait.until(EC.presence_of_element_located((By.ID, 'ap_password'))).send_keys(password)
        wait.until(EC.presence_of_element_located((By.ID, 'ap_password_check'))).send_keys(password)
        wait.until(EC.element_to_be_clickable((By.ID, 'continue'))).click()

        if 'captcha' in driver.page_source.lower() and not solve_captcha(driver, wait):
            await update.message.reply_text(f'CAPTCHA no resuelto. Completa manualmente: {driver.current_url}')
            return ConversationHandler.END

        if 'verify' in driver.current_url:
            await update.message.reply_text(f'Verificación requerida. Revisa tu correo {email} para el código.')
        else:
            await update.message.reply_text(f'¡Registro completado con {email}, nombre {nombre}, y contraseña {password}!')
    except TimeoutException:
        await update.message.reply_text('Timeout. Intenta manualmente.')
    except Exception as e:
        await update.message.reply_text(f'Error: {e}. Intenta manualmente.')
    finally:
        driver.quit()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Cancelado.')
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('crear_cuenta', crear_cuenta)],
        states={EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
