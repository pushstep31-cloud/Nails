# ---------- CSS СТИЛИ ----------
st.markdown("""
    <style>
    /* Нежно-розовый фон */
    .stApp { background-color: #FFF0F5 !important; }
    
    /* Общий текст */
    h1, h2, h3, h4, p, span, div { color: #333333; }
    
    /* Обычные белые кнопки (Настя, Выйти, недели и т.д.) */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #FFB6C1 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    
    /* НЕЖНАЯ ЗЕЛЕНАЯ КНОПКА (Выбранный мастер и кнопка Войти/Сохранить) */
    .stButton > button[kind="primary"] {
        background-color: rgba(46, 125, 50, 0.15) !important; /* Прозрачный зеленый */
        color: #1B5E20 !important; /* Темно-зеленый текст */
        border: 2px solid #2E7D32 !important; /* Четкая зеленая рамка */
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    
    /* Делаем кнопку "Войти" и "Сохранить" чуть крупнее */
    .stButton > button[kind="primary"] {
        height: 50px !important;
        font-size: 1.1em !important;
    }

    /* Поля ввода текста и даты */
    .stTextInput input, .stDateInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 8px !important;
        border: 1px solid #FFB6C1 !important;
    }
    
    /* Убираем красную рамку */
    .stTextInput input:focus, .stDateInput input:focus {
        border-color: #FF69B4 !important;
        box-shadow: none !important;
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
    /* Выбранное время - тоже делаем нежным */
    .time-cell.active {
        background-color: rgba(46, 125, 50, 0.15) !important;
        border: 2px solid #2E7D32 !important;
        color: #1B5E20 !important;
    }
    
    /* Зеленые плашки времени */
    div[data-testid="stAlert"] {
        background-color: rgba(46, 125, 50, 0.15) !important;
        color: #1B5E20 !important;
        border: 1px solid #2E7D32 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stAlert"] p { color: #1B5E20 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)
