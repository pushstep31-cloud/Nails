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
    c.execute(
        "INSERT INTO shifts (master, day, start, end, comment) VALUES (?,?,?,?,?)",
        (master, day, start, end, comment),
    )
    conn.commit()
    conn.close()

def update_shift(shift_id, day, start, end, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "UPDATE shifts SET day=?, start=?, end=?, comment=? WHERE id=?",
        (day, start, end, comment, shift_id),
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

# CSS-стили для кнопок
st.markdown("""
    <style>
    /* Кнопки кубиков */
    div[data-testid="stHorizontalBlock"] button {
        width: 100% !important;
        padding: 10px 0px !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 1.1em !important;
    }
    /* Кнопки при нажатии */
    div[data-testid="stHorizontalBlock"] button:active, div[data-testid="stHorizontalBlock"] button:focus {
        background-color: #E0E0E0 !important;
        border-color: #2E7D32 !important;
    }
    /* Главные кнопки (Сохранить/Выйти) */
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
    /* Зеленая кнопка сохранения */
    div[data-testid="stFormSubmitButton"] button {
        background-color: #2E7D32 !important;
        color: white !important;
        font-size: 1.1em !important;
        height: 50px !important;
        width: 100% !important;
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

# Инициализация выбранного времени (по умолчанию 10:00 и 18:00)
if "sel_start_h" not in st.session_state:
    st.session_state.sel_start_h = 10
    st.session_state.sel_start_m = 0
    st.session_state.sel_end_h = 18
    st.session_state.sel_end_m = 0

# Если нажали "Редактировать", загружаем время в кубики
if st.session_state.edit_id:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT day, start, end, comment FROM shifts WHERE id=?", (st.session_state.edit_id,))
    edit_data = c.fetchone()
    conn.close()
    
    st.session_state.sel_start_h = int(edit_data[1].split(":")[0])
    st.session_state.sel_start_m = int(edit_data[1].split(":")[1])
    st.session_state.sel_end_h = int(edit_data[2].split(":")[0])
    st.session_state.sel_end_m = int(edit_data[2].split(":")[1])
    default_day = datetime.strptime(edit_data[0], "%Y-%m-%d").date()
    default_comment = edit_data[3]
    btn_text = "💾 Обновить смену"
else:
    default_day = date.today()
    default_comment = "Педикюр"
    btn_text = "💾 Сохранить смену"

# --- ДОБАВЛЕНИЕ И РЕДАКТИРОВАНИЕ СМЕНЫ ---
with st.expander("➕ Добавить или изменить смену", expanded=(st.session_state.edit_id is not None)):
    with st.form("shift_form"):
        
        comment = st.text_input("Услуга / Комментарий", value=default_comment)
        selected_day = st.date_input("Дата смены", value=default_day)
        
        # --- БЛОК ВЫБОРА ВРЕМЕНИ НАЧАЛА ---
        st.markdown("#### 🕒 Время начала")
        # Часы (сетка 6 колонок)
        cols_start_h = st.columns(6)
        for i, h in enumerate(range(0, 24)):
            with cols_start_h[i % 6]:
                # Если час выбран, делаем кнопку зеленой (через html)
                if st.form_submit_button(f"{h:02d}", key=f"sh_{h}", help="Выбрать час"):
                    st.session_state.sel_start_h = h
                    st.rerun()
        
        # Минуты
        cols_start_m = st.columns(2)
        with cols_start_m[0]:
            if st.form_submit_button(":00", key="sm_0"):
                st.session_state.sel_start_m = 0
                st.rerun()
        with cols_start_m[1]:
            if st.form_submit_button(":30", key="sm_30"):
                st.session_state.sel_start_m = 30
                st.rerun()
                
        st.info(f"Выбрано начало: **{st.session_state.sel_start_h:02d}:{st.session_state.sel_start_m:02d}**")


        # --- БЛОК ВЫБОРА ВРЕМЕНИ КОНЦА ---
        st.markdown("#### 🕒 Время окончания")
        cols_end_h = st.columns(6)
        for i, h in enumerate(range(0, 24)):
            with cols_end_h[i % 6]:
                if st.form_submit_button(f"{h:02d}", key=f"eh_{h}"):
                    st.session_state.sel_end_h = h
                    st.rerun()
                    
        cols_end_m = st.columns(2)
        with cols_end_m[0]:
            if st.form_submit_button(":00", key="em_0"):
                st.session_state.sel_end_m = 0
                st.rerun()
        with cols_end_m[1]:
            if st.form_submit_button(":30", key="em_30"):
                st.session_state.sel_end_m = 30
                st.rerun()
                
        st.info(f"Выбрано окончание: **{st.session_state.sel_end_h:02d}:{st.session_state.sel_end_m:02d}**")

        st.write("---")
        # Итоговая кнопка
        submitted = st.form_submit_button(btn_text)
        
        if submitted:
            start_str = f"{st.session_state.sel_start_h:02d}:{st.session_state.sel_start_m:02d}"
            end_str = f"{st.session_state.sel_end_h:02d}:{st.session_state.sel_end_m:02d}"
            day_str = selected_day.strftime("%Y-%m-%d")
            
            if start_str >= end_str:
                st.error("Время окончания должно быть позже начала")
            else:
                has_overlap, msg = check_overlap(day_str, start_str, end_str, exclude_id=st.session_state.edit_id)
                if has_overlap:
                    st.error(msg)
                else:
                    if st.session_state.edit_id:
                        update_shift(st.session_state.edit_id, day_str, start_str, end_str, comment)
                        st.success("Смена обновлена!")
                        st.session_state.edit_id = None
                    else:
                        add_shift(master, day_str, start_str, end_str, comment)
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
