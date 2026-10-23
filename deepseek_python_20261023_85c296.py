import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta

# ---------- НАСТРОЙКИ ----------
PASSWORDS = {
    "Мастер 1": "1111",
    "Мастер 2": "2222",
}
COLORS = {
    "Мастер 1": "#4A90D9",
    "Мастер 2": "#D9534F",
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

st.subheader("Выберите день")
selected_day = st.date_input("Дата", value=date.today())
day_str = selected_day.strftime("%Y-%m-%d")

with st.expander("➕ Добавить смену", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        start = st.selectbox("Начало", SLOTS, index=20)
    with col2:
        end = st.selectbox("Конец", SLOTS, index=36)
    comment = st.text_input("Комментарий (необязательно)", placeholder="Например: перерыв 14:00–14:30")
    if st.button("Сохранить смену"):
        if start >= end:
            st.error("Время окончания должно быть позже начала")
        else:
            add_shift(master, day_str, start, end, comment)
            st.success("Смена добавлена")
            st.rerun()

st.subheader(f"Смены на {selected_day.strftime('%d.%m.%Y')}")
shifts = get_shifts(day_str)

if not shifts:
    st.info("На этот день смен пока нет")
else:
    for sid, m, d, s, e, cm in shifts:
        color = COLORS.get(m, "#888")
        st.markdown(
            f"""
            <div style="border-left:6px solid {color}; padding:8px 12px; margin-bottom:8px; background:#f7f7f7; border-radius:6px;">
                <b style="color:{color};">{m}</b> — {s}–{e}<br>
                <span style="font-size:0.9em;">{cm if cm else '—'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if m == master:
            if st.button(f"Удалить смену {s}–{e}", key=f"del_{sid}"):
                delete_shift(sid)
                st.rerun()

st.subheader("Все смены (ближайшие 7 дней)")
today = date.today()
week_later = today + timedelta(days=7)
all_shifts = get_shifts()
week_shifts = [x for x in all_shifts if today.strftime("%Y-%m-%d") <= x[2] <= week_later.strftime("%Y-%m-%d")]

if not week_shifts:
    st.info("На ближайшую неделю смен нет")
else:
    for sid, m, d, s, e, cm in week_shifts:
        color = COLORS.get(m, "#888")
        st.markdown(
            f"""
            <div style="border-left:6px solid {color}; padding:6px 12px; margin-bottom:6px; background:#fafafa; border-radius:6px;">
                <b>{d}</b> — <span style="color:{color};">{m}</span>: {s}–{e} {('· ' + cm) if cm else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )