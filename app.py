import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta

# ---------- НАСТРОЙКИ ----------
PASSWORDS = {
    "Диана": "1111",
    "Настя": "2222",
}
COLORS = {
    "Диана": "#4A90D9",  # синий
    "Настя": "#D9534F",  # красный
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

def update_shift(shift_id, day, start, end, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE shifts SET day=?, start=?, end=?, comment=? WHERE id=?",
              (day, start, end, comment, shift_id))
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

def check_overlap(day, start, end, exclude_id=None):
    existing_shifts = get_shifts(day)
    for sid, m, _, s, e, _ in existing_shifts:
        if exclude_id is not None and sid == exclude_id:
            continue
        if (start < e) and (end > s):
            return True, f"Пересечение: {m} уже работает с {s} до {e}."
    return False, ""

# ---------- ИНТЕРФЕЙС ----------
st.set_page_config(page_title="График мастеров", page_icon="💅", layout="centered")

# CSS-стили
st.markdown("""
    <style>
    /* Стиль для кубиков времени (обычные кнопки) */
    div[data-testid="stHorizontalBlock"] button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 10px 0px !important;
        height: 50px !important;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: #2E7D32 !important;
        color: #2E7D32 !important;
    }
    
    /* Остальные кнопки */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        font-weight: bold !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary p {
        color: #000000 !important;
        font-weight: bold !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

init_db()
st.title("💅 График мастеров")

# --- ЧТЕНИЕ ЛОГИНА ---
if "master" not in st.session_state:
    st.session_state.master = None

if st.session_state.master is None and "user" in st.query_params:
    user_from_url = st.query_params["user"]
    if user_from_url in PASSWORDS:
        st.session_state.master = user_from_url

# --- АВТОРИЗАЦИЯ ---
if st.session_state.master is None:
    st.subheader("Вход")
    login = st.selectbox("Кто вы?", list(PASSWORDS.keys()))
    pwd = st.text_input("Пароль", type="password")
    
    if st.button("Войти"):
        if PASSWORDS.get(login) == pwd:
            st.session_state.master = login
            st.query_params["user"] = login
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

master = st.session_state.master
st.success(f"Вы вошли как **{master}**")

if st.button("Выйти"):
    st.session_state.master = None
    st.query_params.clear()
    st.rerun()

# --- ПЕРЕМЕННЫЕ ДЛЯ РЕДАКТИРОВАНИЯ ---
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "sel_start" not in st.session_state:
    st.session_state.sel_start = "10:00"
    st.session_state.sel_end = "18:00"
    st.session_state.sel_date = date.today()
    st.session_state.sel_comment = "Педикюр"

if st.session_state.edit_id:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT day, start, end, comment FROM shifts WHERE id=?", (st.session_state.edit_id,))
    edit_data = c.fetchone()
    conn.close()
    
    st.session_state.sel_start = edit_data[1]
    st.session_state.sel_end = edit_data[2]
    st.session_state.sel_date = datetime.strptime(edit_data[0], "%Y-%m-%d").date()
    st.session_state.sel_comment = edit_data[3]
    btn_text = "💾 Обновить смену"
else:
    btn_text = "💾 Сохранить смену"

# --- ДОБАВЛЕНИЕ И РЕДАКТИРОВАНИЕ СМЕНЫ ---
with st.expander("➕ Добавить или изменить смену", expanded=(st.session_state.edit_id is not None)):
    
    st.session_state.sel_comment = st.text_input("Услуга / Комментарий", value=st.session_state.sel_comment)
    st.session_state.sel_date = st.date_input("Дата смены", value=st.session_state.sel_date)
    
    # --- ВЫБОР ВРЕМЕНИ НАЧАЛА ---
    st.markdown("#### 🕒 Время начала")
    st.info(f"Выбрано: **{st.session_state.sel_start}**")
    
    # Сетка часов (по 4 штуки в ряд)
    hours = list(range(8, 24)) # с 8 утра до 23 вечера
    for i in range(0, len(hours), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(hours):
                h = hours[i+j]
                # Проверяем, выбран ли этот час
                is_selected = st.session_state.sel_start.startswith(f"{h:02d}:")
                label = f"**{h:02d}**" if is_selected else f"{h:02d}"
                
                if cols[j].button(label, key=f"h_start_{h}", use_container_width=True):
                    current_min = st.session_state.sel_start.split(":")[1]
                    st.session_state.sel_start = f"{h:02d}:{current_min}"
                    st.rerun()
    
    # Минуты
    cols_m = st.columns(2)
    if cols_m[0].button("00 мин", key="m_start_00", use_container_width=True):
        current_h = st.session_state.sel_start.split(":")[0]
        st.session_state.sel_start = f"{current_h}:00"
        st.rerun()
    if cols_m[1].button("30 мин", key="m_start_30", use_container_width=True):
        current_h = st.session_state.sel_start.split(":")[0]
        st.session_state.sel_start = f"{current_h}:30"
        st.rerun()

    st.write("---")
    
    # --- ВЫБОР ВРЕМЕНИ КОНЦА ---
    st.markdown("#### 🕒 Время окончания")
    st.info(f"Выбрано: **{st.session_state.sel_end}**")
    
    for i in range(0, len(hours), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(hours):
                h = hours[i+j]
                is_selected = st.session_state.sel_end.startswith(f"{h:02d}:")
                label = f"**{h:02d}**" if is_selected else f"{h:02d}"
                
                if cols[j].button(label, key=f"h_end_{h}", use_container_width=True):
                    current_min = st.session_state.sel_end.split(":")[1]
                    st.session_state.sel_end = f"{h:02d}:{current_min}"
                    st.rerun()

    cols_m_end = st.columns(2)
    if cols_m_end[0].button("00 мин", key="m_end_00", use_container_width=True):
        current_h = st.session_state.sel_end.split(":")[0]
        st.session_state.sel_end = f"{current_h}:00"
        st.rerun()
    if cols_m_end[1].button("30 мин", key="m_end_30", use_container_width=True):
        current_h = st.session_state.sel_end.split(":")[0]
        st.session_state.sel_end = f"{current_h}:30"
        st.rerun()

    st.write("---")
    
    # Кнопка сохранения
    if st.button(btn_text, use_container_width=True, type="primary"):
        day_str = st.session_state.sel_date.strftime("%Y-%m-%d")
        if st.session_state.sel_start >= st.session_state.sel_end:
            st.error("Время окончания должно быть позже начала")
        else:
            has_overlap, msg = check_overlap(day_str, st.session_state.sel_start, st.session_state.sel_end, exclude_id=st.session_state.edit_id)
            if has_overlap:
                st.error(msg)
            else:
                if st.session_state.edit_id:
                    update_shift(st.session_state.edit_id, day_str, st.session_state.sel_start, st.session_state.sel_end, st.session_state.sel_comment)
                    st.success("Смена обновлена!")
                    st.session_state.edit_id = None
                else:
                    add_shift(master, day_str, st.session_state.sel_start, st.session_state.sel_end, st.session_state.sel_comment)
                    st.success("Смена добавлена!")
                st.rerun()

    if st.session_state.edit_id:
        if st.button("❌ Отменить редактирование"):
            st.session_state.edit_id = None
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

st.markdown(
    f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="font-size: 1.3em; font-weight: 800; color: #FFFFFF;">
            Неделя: {start_of_week.strftime('%d.%m.%Y')} — {end_of_week.strftime('%d.%m.%Y')}
        </span>
    </div>
    """, 
    unsafe_allow_html=True
)

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
            """, 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="margin-top:20px; margin-bottom:10px;">
                <span style="background-color:#E0E0E0; color:#333333; padding:6px 12px; border-radius:6px; font-weight:bold; font-size:1.1em;">
                    {day_title}
                </span>
            </div>
            """, 
            unsafe_allow_html=True
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
                """,
                unsafe_allow_html=True,
            )
            
            if (m == master) or (m in ["Мастер 1", "Мастер 2"]):
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️ Редактировать", key=f"edit_{sid}"):
                        st.session_state.edit_id = sid
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Удалить", key=f"del_{sid}"):
                        delete_shift(sid)
                        if st.session_state.edit_id == sid:
                            st.session_state.edit_id = None
                        st.rerun()
    st.divider()
