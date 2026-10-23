import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import streamlit.components.v1 as components

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
    c.execute("INSERT INTO shifts (master, day, start, end, comment) VALUES (?,?,?,?,?)",
              (master, day, start, end, comment))
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

def check_overlap(day, start, end):
    existing_shifts = get_shifts(day)
    for _, m, _, s, e, _ in existing_shifts:
        if (start < e) and (end > s):
            return True, f"Пересечение с графиком: {m} уже работает с {s} до {e}."
    return False, ""

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

# --- ЧТЕНИЕ СЕССИИ ИЗ БРАУЗЕРА ---
# Этот компонент отправляет сохраненное имя мастера обратно в Streamlit при загрузке
saved_master = components.html(
    """
    <script>
    const saved = localStorage.getItem("master_login");
    if (saved) {
        // Отправляем данные в Streamlit (через костыль с изменением размера фрейма)
        window.parent.postMessage({type: "streamlit:setComponentValue", value: saved}, "*");
    }
    </script>
    """,
    height=0,
)

if "master" not in st.session_state:
    st.session_state.master = None

# Если в браузере есть сохраненный логин, применяем его
if saved_master and st.session_state.master is None:
    st.session_state.master = saved_master

st.title("💅 График мастеров")

# --- Авторизация ---
if st.session_state.master is None:
    st.subheader("Вход")
    login = st.selectbox("Кто вы?", ["Мастер 1", "Мастер 2"])
    pwd = st.text_input("Пароль", type="password")
    
    if st.button("Войти"):
        if PASSWORDS.get(login) == pwd:
            st.session_state.master = login
            # Сохраняем в память браузера
            components.html(
                f"""
                <script>
                localStorage.setItem("master_login", "{login}");
                </script>
                """,
                height=0,
            )
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

master = st.session_state.master
st.success(f"Вы вошли как **{master}**")

if st.button("Выйти"):
    st.session_state.master = None
    # Очищаем память браузера
    components.html(
        """
        <script>
        localStorage.removeItem("master_login");
        </script>
        """,
        height=0,
    )
    st.rerun()

# --- Добавление смены ---
with st.expander("➕ Добавить смену", expanded=False):
    selected_day = st.date_input("Дата смены", value=date.today())
    day_str = selected_day.strftime("%Y-%m-%d")
    
    col1, col2 = st.columns(2)
    with col1:
        start = st.selectbox("Начало", SLOTS, index=20)
    with col2:
        end = st.selectbox("Конец", SLOTS, index=36)
        
    comment = st.text_input("Комментарий (необязательно)", placeholder="Например: перерыв")
    
    if st.button("Сохранить смену"):
        if start >= end:
            st.error("Время окончания должно быть позже начала")
        else:
            has_overlap, msg = check_overlap(day_str, start, end)
            if has_overlap:
                st.error(msg)
            else:
                add_shift(master, day_str, start, end, comment)
                st.success("Смена добавлена!")
                st.rerun()

# --- ЛИСТАНИЕ НЕДЕЛЬ И КАЛЕНДАРЬ ---
st.subheader("📅 График на неделю")

if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("⬅️ Предыдущая неделя"):
        st.session_state.week_offset -= 1
        st.rerun()
with col_next:
    if st.button("Следующая неделя ➡️"):
        st.session_state.week_offset += 1
        st.rerun()

today = date.today()
start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.week_offset)
end_of_week = start_of_week + timedelta(days=6)

st.caption(f"Неделя: {start_of_week.strftime('%d.%m.%Y')} — {end_of_week.strftime('%d.%m.%Y')}")

days_ru = {"Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср", "Thursday": "Чт", "Friday": "Пт", "Saturday": "Сб", "Sunday": "Вс"}

for i in range(7):
    current_day = start_of_week + timedelta(days=i)
    current_day_str = current_day.strftime("%Y-%m-%d")
    
    day_name = current_day.strftime("%A")
    day_title = f"{days_ru.get(day_name, '')}, {current_day.strftime('%d.%m')}"
    
    if current_day == today:
        st.markdown(
            f"""
            <div style="margin-top:20px; margin-bottom:10px;">
                <span style="background-color:#2E7D32; color:white; padding:6px 12px; border-radius:6px; font-weight:bold; font-size:1.2em;">
                    👉 Сегодня, {day_title}
                </span>
            </div>
            """, unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="margin-top:20px; margin-bottom:10px;">
                <span style="background-color:#E0E0E0; color:#333333; padding:6px 12px; border-radius:6px; font-weight:bold; font-size:1.1em;">
                    {day_title}
                </span>
            </div>
            """, unsafe_allow_html=True
        )
    
    day_shifts = get_shifts(current_day_str)
    if not day_shifts:
        st.markdown("<span style='color:#888;'>Выходной / Смен нет</span>", unsafe_allow_html=True)
    else:
        day_shifts = sorted(day_shifts, key=lambda x: x[3])
        for sid, m, d, s, e, cm in day_shifts:
            color = COLORS.get(m, "#888")
            st.markdown(
                f"""
                <div style="border-left:6px solid {color}; padding:8px 10px; margin-bottom:8px; background:#f4f4f4; border-radius:6px;">
                    <b style="color:{color}; font-size:1.1em;">{m}</b><br>
                    <span style="color:#333; font-weight:bold; font-size:1.05em;">{s}–{e}</span>
                    <span style="color:#555; font-size:0.9em;">{(' (' + cm + ')') if cm else ''}</span>
                </div>
                """, unsafe_allow_html=True
            )
            if m == master:
                if st.button(f"Удалить {s}–{e}", key=f"del_{sid}"):
                    delete_shift(sid)
                    st.rerun()
    st.divider()
