# Estilo visual (CSS) para deixar o botão laranja Shopee
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #ee4d2d;
        color: white;
        border-radius: 10px;
        width: 100%;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True) # <-- O ERRO ESTAVA AQUI (HTML, não NAME)
