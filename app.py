import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta

# ---------- НАСТРОЙКИ ----------
PASSWORDS = {
    "Диана": "1111",
    "Настя": "2222",
}
COLORS = {
    "Диана": "#4A90D9",
    "Настя": "#D9534F",
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

# ---------- CSS СТИЛИ ----------
st.markdown("""
    <style>
    /* Нежно-розовый фон */
    .stApp { background-color: #FFF0F5 !important; }
    
    /* Общий текст */
    h1, h2, h3, h4, p, span, div { color: #333333; }
    
    /* Обычные белые кнопки */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #FFB6C1 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    
    /* Прозрачная зеленая кнопка */
    .stButton > button[kind="primary"] {
        background-color: rgba(46, 125, 50, 0.15) !important;
        color: #1B5E20 !important;
        border: 2px solid #2E7D32 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    
    /* Поля ввода */
    .stTextInput input, .stDateInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 8px !important;
        border: 1px solid #FFB6C1 !important;
    }
    
    /* Гармошка */
    div[data-testid="stExpander"] summary {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #FFB6C1 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary p { color: #000000 !important; font-weight: bold !important; }
    div[data-testid="stExpander"] summary svg { fill: #000000 !important; }
    
    /* Сетка времени */
    .time-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        margin-bottom: 10px;
    }
    .time-cell {
        padding: 12px 0;
        text-align: center;
        border: 1px solid #CCCCCC;
        border-radius: 8px;
        background-color: white;
        color: black;
        font-weight: bold;
        font-size: 0.95em;
        cursor: pointer;
    }
    .time-cell.active {
        background-color: rgba(46, 125, 50, 0.15) !important;
        border: 2px solid #2E7D32 !important;
        color: #1B5E20 !important;
    }
    
    /* Плашки времени */
    div[data-testid="stAlert"] {
        background-color: rgba(46, 125, 50, 0.15) !important;
        color: #1B5E20 !important;
        border: 1px solid #2E7D32 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stAlert"] p { color: #1B5E20 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

init_db()
st.title("💅 График мастеров")

# --- АВТОРИЗАЦИЯ ---
if "master" not in st.session_state:
    st.session_state.master = None

if st.session_state.master is None and "user" in st.query_params:
    if st.query_params["user"] in PASSWORDS:
        st.session_state.master = st.query_params["user"]

if st.session_state.master is None:
    st.subheader("Вход")
    st.write("**Кто вы?**")
    
    col1, col2 = st.columns(2)
    
    if "login_choice" not in st.session_state:
        st.session_state.login_choice = "Диана"
        
    with col1:
        if st.session_state.login_choice == "Диана":
            if st.button("Диана 👤", use_container_width=True, type="primary"):
                pass
        else:
            if st.button("Диана 👤", use_container_width=True):
                st.session_state.login_choice = "Диана"
                st.rerun()
                
    with col2:
        if st.session_state.login_choice == "Настя":
            if st.button("Настя 👤", use_container_width=True, type="primary"):
                pass
        else:
            if st.button("Настя 👤", use_container_width=True):
                st.session_state.login_choice = "Настя"
                st.rerun()

    pwd = st.text_input("Пароль", type="password")
    
    if st.button("Войти", use_container_width=True):
        if PASSWORDS.get(st.session_state.login_choice) == pwd:
            st.session_state.master = st.session_state.login_choice
            st.query_params["user"] = st.session_state.login_choice
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

master = st.session_state.master
st.success(f"Вы вошли как **{master}**")
if st.button("Выйти", use_container_width=True):
    st.session_state.master = None
    st.query_params.clear()
    st.rerun()

# --- ПЕРЕМЕННЫЕ ---
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

# --- СЛОТЫ ВРЕМЕНИ ---
ALL_TIME_SLOTS = []
for h in range(8, 24):
    ALL_TIME_SLOTS.append(f"{h:02d}:00")
    ALL_TIME_SLOTS.append(f"{h:02d}:30")

# --- ДОБАВЛЕНИЕ / РЕДАКТИРОВАНИЕ ---
with st.expander("➕ Добавить или изменить смену", expanded=(st.session_state.edit_id is not None)):
    
    st.session_state.sel_comment = st.text_input("Услуга / Комментарий", value=st.session_state.sel_comment)
    st.session_state.sel_date = st.date_input("Дата смены", value=st.session_state.sel_date)
    
    st.markdown("#### 🕒 Время начала")
    start_html = '<div class="time-grid">'
    for t in ALL_TIME_SLOTS:
        active_class = " active" if t == st.session_state.sel_start else ""
        start_html += f'<a href="?t_start={t}" target="_self" style="text-decoration:none;"><div class="time-cell{active_class}">{t}</div></a>'
    start_html += '</div>'
    st.markdown(start_html, unsafe_allow_html=True)
    
    if "t_start" in st.query_params:
        st.session_state.sel_start = st.query_params["t_start"]
        st.query_params.pop("t_start")
        st.rerun()

    st.success(f"Выбрано начало: **{st.session_state.sel_start}**")
    st.write("---")
    
    st.markdown("#### 🕒 Время окончания")
    end_html = '<div class="time-grid">'
    for t in ALL_TIME_SLOTS:
        active_class = " active" if t == st.session_state.sel_end else ""
        end_html += f'<a href="?t_end={t}" target="_self" style="text-decoration:none;"><div class="time-cell{active_class}">{t}</div></a>'
    end_html += '</div>'
    st.markdown(end_html, unsafe_allow_html=True)
    
    if "t_end" in st.query_params:
        st.session_state.sel_end = st.query_params["t_end"]
        st.query_params.pop("t_end")
        st.rerun()

    st.success(f"Выбрано окончание: **{st.session_state.sel_end}**")
    st.write("---")
    
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
        if st.button("❌ Отменить редактирование", use_container_width=True):
            st.session_state.edit_id = None
            st.rerun()

# --- КАЛЕНДАРЬ ---
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
        <span style="font-size: 1.3em; font-weight: 800; color: #333333;">
            Неделя: {start_of_week.strftime('%d.%m.%Y')} — {end_of_week.strftime('%d.%m.%Y')}
        </span>
    </div>
    """, unsafe_allow_html=True
)

days_ru = {"Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср", "Thursday": "Чт", "Friday": "Пт", "Saturday": "Сб", "Sunday": "Вс"}

for i in range(7):
    current_day = start_of_week + timedelta(days=i)
    current_day_str = current_day.strftime("%Y-%m-%d")
    day_name = current_day.strftime("%A")
    day_title = f"{days_ru.get(day_name, '')}, {current_day.strftime('%d.%m')}"
    
    if current_day == today:
        st.markdown(
            f'<div style="margin-top:20px; margin-bottom:10px;"><span style="background-color:#2E7D32; color:white; padding:6px 12px; border-radius:6px; font-weight:bold; font-size:1.2em;">👉 Сегодня, {day_title}</span></div>', 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="margin-top:20px; margin-bottom:10px;"><span style="background-color:#FFFFFF; color:#333333; padding:6px 12px; border-radius:6px; font-weight:bold; font-size:1.1em; border: 1px solid #FFB6C1;">{day_title}</span></div>', 
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
                <div style="border-left:6px solid {color}; padding:8px 10px; margin-bottom:8px; background:#FFFFFF; border-radius:6px; border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;">
                    <b style="color:{color}; font-size:1.1em;">{m}</b><br>
                    <span style="color:#333; font-weight:bold; font-size:1.05em;">{s}–{e}</span>
                    <span style="color:#555; font-size:0.9em;">{(' (' + cm + ')') if cm else ''}</span>
                </div>
                """, unsafe_allow_html=True
            )
            
            if (m == master) or (m in ["Мастер 1", "Мастер 2"]):
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️ Редактировать", key=f"edit_{sid}", use_container_width=True):
                        st.session_state.edit_id = sid
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Удалить", key=f"del_{sid}", use_container_width=True):
                        delete_shift(sid)
                        if st.session_state.edit_id == sid:
                            st.session_state.edit_id = None
                        st.rerun()
    
    # ЗАМЕНА СТАНДАРТНОГО РАЗДЕЛИТЕЛЯ НА РОЗОВЫЙ ПУНКТИР
    st.markdown("<hr style='border: 1px dashed #FFB6C1; margin: 20px 0;'>", unsafe_allow_html=True)
