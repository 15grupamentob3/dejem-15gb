import streamlit as st
import pandas as pd
import gspread
import re

# Configuração da página
st.set_page_config(
    page_title="Consulta DEJEM - 15º GB",
    page_icon="🚒",
    layout="centered"
)

# Estilo personalizado (Cores do Corpo de Bombeiros)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #b91c1c; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    </style>
""", unsafe_allow_html=unsafe_allow_html)

# Cabeçalho
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Bras%C3%A3o_do_Corpo_de_Bombeiros_da_PMESP.png/120px-Bras%C3%A3o_do_Corpo_de_Bombeiros_da_PMESP.png", width=70)
st.title("15º GB — Consulta DEJEM")
st.caption("Sistema de Consulta Operacional de Vagas")

# Função para carregar dados do Google Sheets
@st.cache_data(ttl=300) # Atualiza a cada 5 minutos
def carregar_dados():
    ID_PLANILHA = "1Ug3uJdPwWVfuQDksJz2jkZDwfIViUgNbryRXD-3RGCQ"
    URL = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet="
    abas_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    escala_processada = []
    
    for aba in abas_meses:
        try:
            df = pd.read_csv(URL + aba, skiprows=5)
            df.columns = [str(c).replace('"', '').strip() for c in df.columns]
            
            for _, row in df.iterrows():
                escalado_str = str(row.get('Escalado', '')).strip()
                if not escalado_str or 'não teve inscritos' in escalado_str.lower() or escalado_str == 'nan':
                    continue
                
                match_re = re.search(r'(\d{5,6})', escalado_str)
                re_militar = match_re.group(1) if match_re else "N/A"
                
                escala_processada.append({
                    "Mês": aba,
                    "ID Vaga": str(row.get('ID', '')),
                    "Dia": str(row.get('Dia Sem.', '')),
                    "Início": str(row.get('Data Hora Iní.', '')),
                    "Término": str(row.get('Data Hora Tér.', '')),
                    "Local": str(row.get('Local', '')),
                    "AISP": str(row.get('AISP', '')),
                    "Tipo": str(row.get('Tipo de Escala', '')),
                    "RE": re_militar,
                    "Militar": escalado_str
                })
        except Exception:
            pass
            
    return pd.DataFrame(escala_processada)

# Carrega os dados
with st.spinner("Conectando à planilha do Drive..."):
    df_dejem = carregar_dados()

# Abas de navegação
tipo_busca = st.radio("Selecione o tipo de pesquisa:", ["Por RE / ID Militar", "Por Data", "Por ID da Vaga"], horizontal=True)

st.divider()

if tipo_busca == "Por RE / ID Militar":
    re_input = st.text_input("Digite o RE do Militar (ex: 137501):")
    if st.button("Pesquisar RE") or re_input:
        if re_input:
            resultado = df_dejem[df_dejem['RE'] == re_input.strip()]
            if resultado.empty:
                st.warning(f"Nenhum registro encontrado para o RE: {re_input}")
            else:
                militar = resultado.iloc[0]['Militar']
                st.success(f"**Militar:** {militar}")
                st.info(f"Total de escalas no ano: **{len(resultado)}**")
                
                cols = ['Mês', 'Início', 'Término', 'Local', 'Tipo', 'ID Vaga']
                st.dataframe(resultado[cols], hide_index=True, use_container_width=True)

elif tipo_busca == "Por Data":
    data_input = st.text_input("Digite a data (ex: 01/01/26):")
    if st.button("Pesquisar Data") or data_input:
        if data_input:
            resultado = df_dejem[df_dejem['Início'].str.contains(data_input.strip(), na=False)]
            if resultado.empty:
                st.warning(f"Nenhuma escala encontrada para a data: {data_input}")
            else:
                st.success(f"Total de militares escalados em {data_input}: **{len(resultado)}**")
                cols = ['RE', 'Militar', 'Local', 'Tipo', 'Início', 'Término']
                st.dataframe(resultado[cols], hide_index=True, use_container_width=True)

elif tipo_busca == "Por ID da Vaga":
    id_input = st.text_input("Digite o ID da Vaga (ex: 8138956):")
    if st.button("Pesquisar Vaga") or id_input:
        if id_input:
            resultado = df_dejem[df_dejem['ID Vaga'] == id_input.strip()]
            if resultado.empty:
                st.warning(f"Nenhuma vaga encontrada com o ID: {id_input}")
            else:
                st.dataframe(resultado, hide_index=True, use_container_width=True)
