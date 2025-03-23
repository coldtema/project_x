from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Настройки браузера
def get_cookie(product_url):

    # Настройки браузера
    options = Options()
    options.add_argument("--headless")  # Убрать, если нужно видеть браузер
    options.add_argument("--disable-blink-features=AutomationControlled")  # Скрываем факт автоматизации
    options.add_argument("start-maximized")

    # Запускаем браузер
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Открываем страницу
    driver.get(product_url)

    # Ждем, пока загрузится важный элемент (например, кнопка "Купить")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "price"))
        )
    except:
        print("Не дождались загрузки страницы")

    # Достаем cookies
    cookies = driver.get_cookies()

    # Закрываем браузер
    driver.quit()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    print(cookies_dict)
    return cookies_dict
