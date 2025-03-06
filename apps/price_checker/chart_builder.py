import matplotlib
matplotlib.use("Agg") # Устанавливаем без GUI-бэкенда
import matplotlib.pyplot as plt
import pandas as pd

def plot_price_history(dates, prices, filename='apps/price_checker/static/price_checker/chart.png'):
    """
    Функция строит график изменения цены.

    :param dates: список дат (datetime или строки, которые можно преобразовать в datetime)
    :param prices: список цен (числовые значения)
    """
    # Преобразуем даты в формат datetime (если они строковые)
    dates = pd.to_datetime(dates)

    # Создаём график
    plt.figure(figsize=(10, 5))  # Размер графика
    plt.plot(dates, prices, marker="o", linestyle="-", color="b", label="Цена")

    # Настройки
    plt.xlabel("Дата")
    plt.ylabel("Цена")
    plt.title("Изменение цены со временем")
    plt.xticks(rotation=45)  # Поворот подписей по оси X
    plt.grid(False)
    plt.legend()
    print(filename)
    plt.savefig(filename, format="png")  # Сохраняем в файл
    print('сохранено')
    plt.close()