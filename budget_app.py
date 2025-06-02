import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

st.set_page_config(page_title="Бюджет компании", page_icon="📊", initial_sidebar_state="expanded")

FILE_NAME = "budget_data.xlsx"
USERS_FILE = "users.json"
SPRAVOCHNIK_FILE = "spravochnik.xlsx"

# Загрузка справочника статей и подстатей
@st.cache_data
def load_spravochnik():
    if os.path.exists(SPRAVOCHNIK_FILE):
        return pd.read_excel(SPRAVOCHNIK_FILE)
    else:
        return pd.DataFrame(columns=["Категория", "Счет", "Статья", "Подстатья"])

USERS = {
    "admin": "admin123456",
    "supervisor": "supervisor123"
}
ROLES = {
    "admin": "admin",
    "supervisor": "supervisor"
}
MODULES = ["Бюджет", "Продажи", "Отчёты"]

current_year = datetime.now().year
current_month = datetime.now().month
years = list(range(2020, current_year + 2))
month_names = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

# Функции определяем перед их использованием
def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_excel(FILE_NAME)
    else:
        return pd.DataFrame(columns=["Дата", "Категория", "Сумма", "Тип", "Отдел"])

def save_data(data):
    data.to_excel(FILE_NAME, index=False)

def load_users_data():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return (
                data.get("users", USERS.copy()),
                data.get("roles", ROLES.copy()),
                data.get("permissions", {})
            )
        except Exception as e:
            st.warning(f"users.json повреждён или невалиден: {e}. Будет создан новый файл по умолчанию.")
            save_users_data(USERS.copy(), ROLES.copy(), {})
            return USERS.copy(), ROLES.copy(), {}
    else:
        return USERS.copy(), ROLES.copy(), {}

def save_users_data(users, roles, permissions):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users, "roles": roles, "permissions": permissions}, f, ensure_ascii=False, indent=2)

def login():
    st.sidebar.header("Вход")
    with st.sidebar.form("login_form", clear_on_submit=False):
        username = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        submit = st.form_submit_button("Войти")
    if submit:
        users = st.session_state.get("users", USERS)
        roles = st.session_state.get("roles", ROLES)
        # Привести логин и пароль к строке и убрать пробелы
        username = str(username).strip()
        password = str(password).strip()
        # Исправление: при создании пользователя пароль может быть сохранён с пробелами или типом не str
        # Проверяем users.keys() и users.values() явно
        if username in users.keys():
            stored_pass = users[username]
            if stored_pass is None:
                st.error("Ошибка: у пользователя не задан пароль. Обратитесь к администратору.")
                return
            stored_pass = str(stored_pass).strip()
            if stored_pass == password:
                st.session_state["user"] = username
                st.session_state["role"] = roles.get(username, "user")
                st.success(f"Добро пожаловать, {username}!")
                st.rerun()
            else:
                st.error("Неверный логин или пароль")
        else:
            st.error("Неверный логин или пароль")

# Домашняя страница и авторизация
if "user" not in st.session_state:
    # Всегда обновлять пользователей из файла перед login
    users, roles, permissions = load_users_data()
    st.session_state["users"] = users
    st.session_state["roles"] = roles
    st.session_state["permissions"] = permissions
    st.sidebar.title("Меню")
    login()
    st.image("https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=400&q=80", width=200)
    st.title("Добро пожаловать в систему бюджетирования компании!")
    st.markdown("""
    ### Возможности:
    - Вход для сотрудников отделов и администратора
    - Ведение и анализ бюджета по отделам
    - Консолидация бюджета для администратора
    - Графики и фильтры по периодам и отделам
    
    Для начала работы войдите в свой аккаунт через меню слева.
    """)
    st.stop()

user = st.session_state["user"]
role = st.session_state["role"]

# Кнопка выхода
st.sidebar.title("Меню")
if st.sidebar.button("Выйти"):
    st.session_state.clear()
    st.rerun()

# --- Управление пользователями (только для админа) ---
def manage_users():
    st.title("🔑 Управление пользователями и ролями")
    st.subheader("Создать новый профиль пользователя")
    new_username = st.text_input("Логин (имя пользователя)")
    new_password = st.text_input("Пароль", type="password")
    module_perms = {}
    for m in MODULES:
        module_perms[m] = st.selectbox(f"Права для модуля '{m}'", ["editor", "viewer"], key=f"perm_{m}")
    if st.button("Создать пользователя"):
        new_username = str(new_username).strip()
        new_password = str(new_password).strip()
        if not new_username or not new_password:
            st.error("Логин и пароль не должны быть пустыми!")
        elif new_username in st.session_state.get("users", USERS):
            st.error("Пользователь с таким именем уже существует!")
        else:
            users = st.session_state.get("users", USERS).copy()
            roles = st.session_state.get("roles", ROLES).copy()
            permissions = st.session_state.get("permissions", {}).copy()
            users[new_username] = new_password
            roles[new_username] = "custom"
            permissions[new_username] = module_perms
            try:
                save_users_data(users, roles, permissions)
                # После сохранения перечитываем users.json и обновляем session_state
                users2, roles2, permissions2 = load_users_data()
                st.session_state["users"] = users2
                st.session_state["roles"] = roles2
                st.session_state["permissions"] = permissions2
                st.success(f"Пользователь {new_username} создан и сохранён!")
            except Exception as e:
                st.error(f"Ошибка при сохранении пользователя: {e}")
    st.subheader("Список пользователей и прав по модулям")
    users = st.session_state.get("users", USERS)
    permissions = st.session_state.get("permissions", {})
    table = []
    for u in users:
        row = [u]
        for m in MODULES:
            row.append(permissions.get(u, {}).get(m, "editor" if ROLES.get(u, "editor") == "editor" else "viewer"))
        table.append(row)
    st.table(pd.DataFrame(table, columns=["Пользователь"] + MODULES))

# --- Проверка прав пользователя на модуль ---
def get_module_permission(user, module):
    if user == "admin":
        return "editor"
    if user == "supervisor":
        return "viewer_all"
    permissions = st.session_state.get("permissions", {})
    return permissions.get(user, {}).get(module, ROLES.get(user, "editor"))

# --- МЕНЮ ERP ---
menu_items = MODULES + ["Настройки пользователя"]
if role == "admin":
    menu_items.insert(0, "Управление пользователями")
menu = st.sidebar.radio("Выберите модуль:", menu_items)

# --- Настройки пользователя ---
def user_settings():
    st.title("⚙️ Настройки пользователя")
    st.subheader(f"Текущий логин: {user}")
    users = st.session_state.get("users", USERS).copy()
    roles = st.session_state.get("roles", ROLES).copy()
    permissions = st.session_state.get("permissions", {}).copy()
    # Смена пароля
    st.markdown("**Смена пароля**")
    old_pass = st.text_input("Текущий пароль", type="password", key="old_pass")
    new_pass = st.text_input("Новый пароль", type="password", key="new_pass")
    if st.button("Сменить пароль"):
        old_pass = str(old_pass).strip()
        new_pass = str(new_pass).strip()
        stored_pass = str(users.get(user, "")).strip()
        if stored_pass == old_pass:
            users[user] = new_pass
            st.session_state["users"] = users
            save_users_data(users, roles, permissions)
            st.success("Пароль успешно изменён!")
        else:
            st.error("Неверный текущий пароль!")
    # Смена логина
    st.markdown("**Смена логина**")
    new_login = st.text_input("Новый логин", key="new_login")
    if st.button("Сменить логин"):
        if not new_login or new_login in users:
            st.error("Некорректный или уже существующий логин!")
        else:
            old_pass = str(old_pass).strip()
            stored_pass = str(users.get(user, "")).strip()
            if stored_pass != old_pass:
                st.error("Для смены логина введите верный текущий пароль выше!")
            else:
                users[new_login] = users.pop(user)
                roles[new_login] = roles.pop(user)
                # Переносим права
                if user in permissions:
                    permissions[new_login] = permissions.pop(user)
                st.session_state["users"] = users
                st.session_state["roles"] = roles
                st.session_state["permissions"] = permissions
                save_users_data(users, roles, permissions)
                st.success("Логин успешно изменён! Пожалуйста, войдите заново.")
                st.session_state.clear()
                st.rerun()

if menu == "Настройки пользователя":
    user_settings()

elif menu == "Управление пользователями" and role == "admin":
    manage_users()

elif menu == "Бюджет":
    st.title("📊 Бюджет компании по отделам")
    perm = get_module_permission(user, "Бюджет")
    sprav = load_spravochnik()
    if perm == "editor":
        st.subheader(f"Ваш отдел: {user}")
        st.subheader("➕ Добавить запись")
        year = st.selectbox("Год", years, index=years.index(current_year))
        month_name = st.selectbox("Месяц", month_names, index=current_month - 1)
        # Выбор категории и статьи из справочника
        category = st.selectbox("Категория", sorted(sprav["Категория"].dropna().unique()))
        statya_list = sprav[sprav["Категория"] == category]["Статья"].dropna().unique()
        statya = st.selectbox("Статья", sorted(statya_list))
        podstatya_list = sprav[(sprav["Категория"] == category) & (sprav["Статья"] == statya)]["Подстатья"].dropna().unique()
        subcategory = st.selectbox("Подстатья", sorted(podstatya_list))
        amount = st.number_input("Сумма", step=0.01)
        entry_type = st.selectbox("Тип", ["Доход", "Расход"])
        if st.button("Добавить"):
            date_str = f"{year}-{month_name}"
            new_row = {
                "Дата": date_str,
                "Категория": category,
                "Статья": statya,
                "Подстатья": subcategory,
                "Сумма": amount,
                "Тип": entry_type,
                "Отдел": user
            }
            df = load_data()
            if "Подстатья" not in df.columns:
                df["Подстатья"] = ""
            if "Статья" not in df.columns:
                df["Статья"] = ""
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Запись добавлена!")
        df = load_data()
        if "Подстатья" not in df.columns:
            df["Подстатья"] = ""
        df = df[df["Отдел"] == user]
        if not df.empty:
            pivot = df.pivot_table(index=["Категория", "Подстатья"], columns="Дата", values="Сумма", aggfunc="sum", fill_value=0)
            st.dataframe(pivot)
        else:
            st.info("Нет данных для отображения.")
    elif perm == "viewer":
        st.subheader(f"Ваш отдел: {user}")
        sprav = load_spravochnik()
        df = load_data()
        if "Подстатья" not in df.columns:
            df["Подстатья"] = ""
        if "Статья" not in df.columns:
            df["Статья"] = ""
        df = df[df["Отдел"] == user]
        # Фильтры по справочнику
        category_options = sorted(sprav["Категория"].dropna().unique())
        category = st.selectbox("Категория", ["Все"] + category_options)
        if category != "Все":
            df = df[df["Категория"] == category]
            statya_options = sorted(sprav[sprav["Категория"] == category]["Статья"].dropna().unique())
        else:
            statya_options = sorted(sprav["Статья"].dropna().unique())
        statya = st.selectbox("Статья", ["Все"] + statya_options)
        if statya != "Все":
            df = df[df["Статья"] == statya]
            podstatya_options = sorted(sprav[(sprav["Категория"] == category) & (sprav["Статья"] == statya)]["Подстатья"].dropna().unique())
        else:
            podstatya_options = sorted(sprav["Подстатья"].dropna().unique())
        subcategory = st.selectbox("Подстатья", ["Все"] + podstatya_options)
        if subcategory != "Все":
            df = df[df["Подстатья"] == subcategory]
        if not df.empty:
            pivot = df.pivot_table(index=["Категория", "Статья", "Подстатья"], columns="Дата", values="Сумма", aggfunc="sum", fill_value=0)
            st.dataframe(pivot)
        else:
            st.info("Нет данных для отображения.")
    elif perm == "viewer_all":
        st.subheader("Бюджет всех отделов (только просмотр)")
        df = load_data()
        if "Подстатья" not in df.columns:
            df["Подстатья"] = ""
        if not df.empty:
            pivot = df.pivot_table(index=["Категория", "Подстатья", "Отдел"], columns="Дата", values="Сумма", aggfunc="sum", fill_value=0)
            st.dataframe(pivot)
        else:
            st.info("Нет данных для отображения.")
    elif role == "admin":
        st.subheader("Консолидация по всем отделам")
        df = load_data()
        st.dataframe(df)
        st.subheader("💰 Общий баланс")
        income = df[df["Тип"] == "Доход"]["Сумма"].sum()
        expense = df[df["Тип"] == "Расход"]["Сумма"].sum()
        balance = income - expense
        st.markdown(f"**Доходы:** {income} сум  \n**Расходы:** {expense} сум  \n**Остаток:** {balance} сум")
        st.subheader("Баланс по отделам")
        for otdel in df["Отдел"].unique():
            if otdel == "admin":
                continue
            dfo = df[df["Отдел"] == otdel]
            inc = dfo[dfo["Тип"] == "Доход"]["Сумма"].sum()
            exp = dfo[dfo["Тип"] == "Расход"]["Сумма"].sum()
            bal = inc - exp
            st.markdown(f"**{otdel}** — Доход: {inc} | Расход: {exp} | Остаток: {bal}")

elif menu == "Продажи":
    st.title("💵 Модуль продаж")
    perm = get_module_permission(user, "Продажи")
    if perm == "editor":
        st.subheader("➕ Добавить продажу")
        product = st.text_input("Товар/услуга")
        qty = st.number_input("Количество", step=1, min_value=1)
        price = st.number_input("Цена за единицу", step=0.01)
        client = st.text_input("Покупатель")
        if st.button("Сохранить продажу"):
            st.success("Продажа добавлена (демо)")
    elif perm == "viewer_all":
        st.subheader("История продаж всех отделов (демо)")
        st.info("Здесь будет таблица продаж всех отделов.")
    st.subheader("История продаж (демо)")
    st.info("Здесь будет таблица продаж.")
