import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta

st.set_page_config(page_title="График", layout="centered")

PASSWORDS = {"Диана": "1111", "Настя": "2222"}
COLORS = {"Диана": "#4A90D9", "Настя": "#D9534F"}
DB = "schedule.db"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    .stApp { background-color: #FCF8F9 !important; }
    h1, h2, h3, h4, p, span, div { color: #2C2C2C; }
    .stButton > button { background-color: #FFFFFF !important; color: #2C2C2C !important; border: none !important; border-radius: 16px !important; font-weight: 600 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; padding: 10px 20px !important; }
    .stButton > button[kind="primary"] { background-color: #E8F5E9 !important; color: #1B5E20 !important; box-shadow: inset 0 0 0 2px #A5D6A7 !important; }
    .stTextInput input, .stDateInput input { background-color: #FFFFFF !important; color: #2C2C2C !important; border-radius: 16px !important; border: none !important; padding: 12px 16px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.04) !important; }
    div[data-testid="stExpander"] summary { background-color: #FFFFFF !important; color: #2C2C2C !important; border: none !important; border-radius: 16px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; padding: 12px 16px !important; }
    div[data-testid="stExpander"] summary p { font-weight: 600 !important; }
    .time-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; }
    .time-cell { padding: 14px 0; text-align: center; border: none; border-radius: 12px; background-color: white; color: #2C2C2C; font-weight: 600; font-size: 0.95em; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .time-cell.active { background-color: #E8F5E9 !important; color: #1B5E20 !important; box-shadow: inset 0 0 0 2px #A5D6A7 !important; }
    div[data-testid="stAlert"] { background-color: #E8F5E9 !important; color: #1B5E20 !important; border: none !important; border-radius: 16px !important; box-shadow: inset 0 0 0 2px #A5D6A7 !important; }
    </style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT, master TEXT, day TEXT, start TEXT, end TEXT, comment TEXT)")
    conn.commit()
    conn.close()

def add_shift(master, day, start, end, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO shifts (master, day, start, end, comment) VALUES (?,?,?,?,?)", (master, day, start, end, comment))
    conn.commit()
    conn.close()

def update_shift(shift_id, day, start, end, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE shifts SET day=?, start=?, end=?, comment=? WHERE id=?", (day, start, end, comment, shift_id))
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
    for sid, m, _, s, e, _ in get_shifts(day):
        if exclude_id and sid == exclude_id:
            continue
        if (start < e) and (end > s):
            return True, f"Пересечение: {m} уже работает с {s} до {e}."
    return False, ""

init_db()
st.title("💅 График мастеров")

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
        if st.button("Диана 👤", use_container_width=True, type="primary" if st.session_state.login_choice == "Диана" else "secondary"):
            st.session_state.login_choice = "Диана"
            st.rerun()
    with col2:
        if st.button("Настя 👤", use_container_width=True, type="primary" if st.session_state.login_choice == "Настя" else "secondary"):
            st.session_state.login_choice = "Настя"
            st.rerun()
    pwd = st.text_input("Пароль", type="password")
    if st.button("Войти", use_container_width=True, type="primary"):
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

if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "sel_start" not in st.session_state: st.session_state.sel_start = "10:00"
if "sel_end" not in st.session_state: st.session_state.sel_end = "18:00"
if "sel_date" not in st.session_state: st.session_state.sel_date = date.today()
if "sel_comment" not in st.session_state: st.session_state.sel_comment = "Педикюр"

if st.session_state.edit_id:
    data = [x for x in get_shifts() if x[0] == st.session_state.edit_id][0]
    st.session_state.sel_start, st.session_state.sel_end, st.session_state.sel_comment = data[3], data[4], data[5]
    st.session_state.sel_date = datetime.strptime(data[2], "%Y-%m-%d").date()
    btn_text = "💾 Обновить смену"
else:
    btn_text = "💾 Сохранить смену"

ALL_TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(8, 24) for m in (0, 30)]

with st.expander("➕ Добавить или изменить смену", expanded=(st.session_state.edit_id is not None)):
    st.session_state.sel_comment = st.text_input("Услуга / Комментарий", value=st.session_state.sel_comment)
    st.session_state.sel_date = st.date_input("Дата смены", value=st.session_state.sel_date)
    
    st.markdown("#### 🕒 Время начала")
    html_start = '<div class="time-grid">'
    for t in ALL_TIME_SLOTS:
        act = " active" if t == st.session_state.sel_start else ""
        html_start += f'<a href="?t_start={t}" target="_self" style="text-decoration:none;"><div class="time-cell{act}">{t}</div></a>'
    html_start += '</div>'
    st.markdown(html_start, unsafe_allow_html=True)
    if "t_start" in st.query_params:
        st.session_state.sel_start = st.query_params["t_start"]; st.query_params.pop("t_start"); st.rerun()
    st.success(f"Выбрано начало: **{st.session_state.sel_start}**")
    st.write("---")
    
    st.markdown("#### 🕒 Время окончания")
    html_end = '<div class="time-grid">'
    for t in ALL_TIME_SLOTS:
        act = " active" if t == st.session_state.sel_end else ""
        html_end += f'<a href="?t_end={t}" target="_self" style="text-decoration:none;"><div class="time-cell{act}">{t}</div></a>'
    html_end += '</div>'
    st.markdown(html_end, unsafe_allow_html=True)
    if "t_end" in st.query_params:
        st.session_state.sel_end = st.query_params["t_end"]; st.query_params.pop("t_end"); st.rerun()
    st.success(f"Выбрано окончание: **{st.session_state.sel_end}**")
    st.write("---")
    
    if st.button(btn_text, use_container_width=True, type="primary"):
        if st.session_state.sel_start >= st.session_state.sel_end:
            st.error("Время окончания должно быть позже начала")
        else:
            ov, msg = check_overlap(st.session_state.sel_date.strftime("%Y-%m-%d"), st.session_state.sel_start, st.session_state.sel_end, st.session_state.edit_id)
            if ov: st.error(msg)
            else:
                if st.session_state.edit_id:
                    update_shift(st.session_state.edit_id, st.session_state.sel_date.strftime("%Y-%m-%d"), st.session_state.sel_start, st.session_state.sel_end, st.session_state.sel_comment)
                    st.session_state.edit_id = None
                else:
                    add_shift(master, st.session_state.sel_date.strftime("%Y-%m-%d"), st.session_state.sel_start, st.session_state.sel_end, st.session_state.sel_comment)
                st.rerun()
    if st.session_state.edit_id:
        if st.button("❌ Отменить", use_container_width=True):
            st.session_state.edit_id = None; st.rerun()

st.subheader("📅 График на неделю")
if "week_offset" not in st.session_state: st.session_state.week_offset = 0
c1, c2 = st.columns(2)
if c1.button("⬅️ Назад"): st.session_state.week_offset -= 1; st.rerun()
if c2.button("Вперед ➡️"): st.session_state.week_offset += 1; st.rerun()

today = date.today()
start_week = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.week_offset)
st.markdown(f"<div style='text-align:center; margin-bottom:24px;'><span style='font-size:1.3em; font-weight:700;'>Неделя: {start_week.strftime('%d.%m.%Y')} — {(start_week + timedelta(days=6)).strftime('%d.%m.%Y')}</span></div>", unsafe_allow_html=True)

days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
for i in range(7):
    curr = start_week + timedelta(days=i)
    curr_str = curr.strftime("%Y-%m-%d")
    title = f"{days_ru[i]}, {curr.strftime('%d.%m')}"
    
    if curr == today:
        st.markdown(f'<div style="margin-top:24px; margin-bottom:12px;"><span style="background-color:#E8F5E9; color:#1B5E20; padding:8px 16px; border-radius:20px; font-weight:600; box-shadow: inset 0 0 0 2px #A5D6A7;">👉 Сегодня, {title}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="margin-top:24px; margin-bottom:12px;"><span style="background-color:#FFFFFF; padding:8px 16px; border-radius:20px; font-weight:600; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">{title}</span></div>', unsafe_allow_html=True)
    
    shifts = get_shifts(curr_str)
    if not shifts:
        st.markdown("<span style='color:#999; font-size:0.9em; margin-left:8px;'>Выходной / Смен нет</span>", unsafe_allow_html=True)
    else:
        for sid, m, _, s, e, cm in sorted(shifts, key=lambda x: x[3]):
            st.markdown(f'<div style="padding:16px; margin-bottom:12px; background:#FFFFFF; border-radius:16px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); border-left: 6px solid {COLORS.get(m, "#888")};"><b style="color:{COLORS.get(m, "#888")}; font-size:1.1em;">{m}</b><br><span style="font-weight:600; font-size:1.05em;">{s}–{e}</span> <span style="color:#777; font-size:0.9em;">{("(" + cm + ")") if cm else ""}</span></div>', unsafe_allow_html=True)
            if m == master:
                ec, dc = st.columns(2)
                if ec.button("✏️ Изменить", key=f"e_{sid}", use_container_width=True): st.session_state.edit_id = sid; st.rerun()
                if dc.button("🗑️ Удалить", key=f"d_{sid}", use_container_width=True): delete_shift(sid); st.rerun()
