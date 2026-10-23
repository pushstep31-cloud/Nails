import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta

# ---------- НАСТРОЙКИ ----------
PASSWORDS = {
    "Мастер 1": "1111",
    "Мастер 2": "2222",
}
COLORS = {
    "Мастер 1": "#4A90D9",  # синий
    "Мастер 2": "#D9534F",  # красный
}
DB = "schedule.db"

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master TEXT NOT NULL,
            day TEXT NOT NULL,
            start TEXT NOT NULL,
            end TEXT NOT NULL,
            comment TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

def add_shift(master, day, start, end, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO shifts (master, day, start, end, comment) VALUES (?,?,?,?,?)",
        (master, day, start, end, comment),
    )
    conn.commit()
    conn.close()

def get_shifts(day=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if day:
        c.execute("SELECT id, master, day, start, end, comment FROM shifts WHERE day=? ORDER BY start", (day,))
    else:
        c.execute("SELECT id, master, day, start, end, comment FROM shifts ORDER BY day, start")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_shift(shift_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM shifts WHERE id=?", (shift_id,))
    conn.commit()
    conn.close()

# ---------- СЛОТЫ 24Ч x 30МИН ----------
def time_slots():
    slots = []
    t = datetime.strptime("00:00", "%H:%M")
    for _ in range(48):
        slots.append(t.strftime("%H:%M"))
        t += timedelta(minutes=30)
    return slots

SLOTS = time_slots()

# ---------- ИНТЕРФЕЙС ----------
st.set_page_config(page_title="График мастеров", page_icon="💅", layout="centered")
init_db()

st.title("💅 График мастеров")

# --- Авторизация ---
if "master" not in st.session_state:
    st.session_state.master = None

if st.session_state.master is None:
    st.subheader("Вход")
    login = st.selectbox("Кто вы?", ["Мастер 1", "Мастер 2"])
    pwd = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        if PASSWORDS.get(login) == pwd:
            st.session_state.master = login
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

master = st.session_state.master
st.success(f"Вы вошли как **{master}**")
if st.button("Выйти"):
    st.session_state.master = None
    st.rerun()

# --- Добавление смены (в свернутом блоке) ---
with st.expander("➕ Добавить смену", expanded=False):
    selected_day = st.date_input("Дата смены", value=date.today())
    day_str = selected_day.strftime("%Y-%m-%d")
    
    col1, col2 = st.columns(2)
    with col1:
        start = st.selectbox("Начало", SLOTS, index=20)  # 10:00
    with col2:
        end = st.selectbox("Конец", SLOTS, index=36)    # 18:00
        
    comment = st.text_input("Комментарий (необязательно)", placeholder="Например: перерыв 14:00–14:30")
    
    if st.button("Сохранить смену"):
        if start >= end:
            st.error("Время окончания должно быть позже начала")
        else:
            add_shift(master, day_str, start, end, comment)
            st.success("Смена добавлена!")
            st.rerun()

# --- ЛИСТАНИЕ НЕДЕЛЬ И КАЛЕНДАРЬ ---
st.subheader("📅 График на неделю")

# Инициализация текущей недели в сессии, чтобы запоминать листание
if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

# Кнопки переключения недель
col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("⬅️ Предыдущая неделя"):
        st.session_state.week_offset -= 1
        st.rerun()
with col_next:
    if st.button("Следующая неделя ➡️"):
        st.session_state.week_offset += 1
        st.rerun()

# Вычисляем даты для отображаемой недели
today = date.today()
start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.week_offset)
end_of_week = start_of_week + timedelta(days=6)

# Показываем диапазон дат
st.caption(f"Неделя: {start_of_week.strftime('%d.%m.%Y')} — {end_of_week.strftime('%d.%m.%Y')}")

days_ru = {"Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср", "Thursday": "Чт", "Friday": "Пт", "Saturday": "Сб", "Sunday": "Вс"}

# Проходимся по 7 дням недели
for i in range(7):
    current_day = start_of_week + timedelta(days=i)
    current_day_str = current_day.strftime("%Y-%m-%d")
    
    day_name = current_day.strftime("%A")
    day_label = f"**{days_ru.get(day_name, '')}, {current_day.strftime('%d.%m')}**"
    
    if current_day == today:
        day_label = f"👉 **Сегодня, {current_day.strftime('%d.%m')}**"
        
    st.markdown(f"### {day_label}")
    
    day_shifts = get_shifts(current_day_str)
    if not day_shifts:
        st.caption("Выходной / Смен нет")
    else:
        for sid, m, d, s, e, cm in day_shifts:
            color = COLORS.get(m, "#888")
            st.markdown(
                f"""
                <div style="border-left:6px solid {color}; padding:6px 10px; margin-bottom:6px; background:#f4f4f4; border-radius:4px;">
                    <b style="color:{color};">{m}</b>: {s}–{e} 
                    <span style="font-size:0.85em; color:#555;">{('(' + cm + ')') if cm else ''}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Кнопка удаления только для своих смен
            if m == master:
                if st.button(f"Удалить {s}–{e}", key=f"del_{sid}"):
                    delete_shift(sid)
                    st.rerun()
    st.divider()
