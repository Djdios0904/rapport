import streamlit as st
import pandas as pd

# Hjælpefunktioner til datarensning
def clean_antal(val):
    s = str(val).strip()
    if s == '03.feb': return 3.0
    s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

def clean_numeric(val):
    if pd.isna(val): return 0.0
    # Rens for ' kr.', fjern tusindtals-punktum, og skift decimal-komma til punktum
    s = str(val).replace(' kr.', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

# App layout
st.set_page_config(page_title="Behandler Statistik", layout="wide")
st.title("📊 Behandler Produktions-Opgørelse")
st.write("Tal er afrundet til hele tal. Komma bruges som tusindtals-separator.")

uploaded_file = st.file_uploader("Vælg CSV-fil", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=';', encoding='latin-1')
    
    # Rens data
    df['Antal_clean'] = df['Antal'].apply(clean_antal)
    df['Beløb_clean'] = df['Beløb'].apply(clean_numeric)
    df['Ialt_clean'] = df['Ialt'].apply(clean_numeric)
    df['Kode'] = df['Kode'].astype(str).str.strip()

    # Kodelister
    codes_behandlinger = ['1035', '10350', '1036g', '1036', '1036p', '1037', '1042', '1043', '1044', '1045', '1052', '1053', '1054', '1055', '1062', '1063', '1065']
    codes_nye = ['1015', '10150', '1016', '1040', '1041', '1050', '1051', '1060', '1061']
    codes_1017 = ['1017', '1017p', '1017g', '10170']
    codes_roentgen = ['2014', '20140', '2015']
    codes_ultralyd = ['2030', '20300']
    codes_aku = ['aku', 'akup']
    codes_chokboelge = ['9806', 'CB']

    def calculate_stats(group):
        behandlinger = group[group['Kode'].isin(codes_behandlinger)]['Antal_clean'].sum()
        nye = group[group['Kode'].isin(codes_nye)]['Antal_clean'].sum()
        sum_1017 = group[group['Kode'].isin(codes_1017)]['Antal_clean'].sum()
        roentgen = group[group['Kode'].isin(codes_roentgen)]['Antal_clean'].sum()
        ultralyd = group[group['Kode'].isin(codes_ultralyd)]['Antal_clean'].sum()
        billeddiagnostik = roentgen + ultralyd
        akupunktur = group[group['Kode'].str.lower().isin(codes_aku)]['Antal_clean'].sum()
        
        chok_rows = group[group['Kode'].isin(codes_chokboelge)]
        chok_antal = chok_rows['Antal_clean'].sum()
        chok_kr = chok_rows['Beløb_clean'].sum()
        
        total_omsætning = group['Ialt_clean'].sum()
        pva = (behandlinger / nye) if behandlinger != 0 else 0
        
        return pd.Series({
            'Behandlinger': int(round(behandlinger)),
            'Nye': int(round(nye)),
            '1017 samlet': int(round(sum_1017)),
            'Røntgen': int(round(roentgen)),
            'Ultralyd': int(round(ultralyd)),
            'Billeddiagnostik': int(round(billeddiagnostik)),
            'Akupunktur': int(round(akupunktur)),
            'Chokbølge (Antal)': int(round(chok_antal)),
            'Chokbølge (kr.)': int(round(chok_kr)),
            'PVA (%)': int(round(pva)),
            'Total Omsætning': int(round(total_omsætning))
            
        })

    # Beregn per behandler
    result = df.groupby('Behandler').apply(calculate_stats).reset_index()

    # Beregn TOTAL-række
    numeric_cols = result.select_dtypes(include=['number']).columns
    total_values = result[numeric_cols].sum()
    
    # Korrekt PVA for totalen
    if total_values['Behandlinger'] != 0:
        total_pva = int(round((total_values['Nye'] / total_values['Behandlinger']) * 100))
    else:
        total_pva = 0
    
    total_row = total_values.to_dict()
    total_row['Behandler'] = 'TOTAL'
    total_row['PVA (%)'] = total_pva
    
    result = pd.concat([result, pd.DataFrame([total_row])], ignore_index=True)

    # Visning i Streamlit - vi fjerner de avancerede formateringer og bruger standard
    st.subheader("Opgørelse pr. behandler")
    
    # Vi bruger en meget simpel formatering her:
    st.dataframe(
        result,
        use_container_width=True,
        column_config={
            col: st.column_config.NumberColumn(step=1, format="%d") for col in numeric_cols
        }
    )

    # Download
    csv = result.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.download_button("Download resultat som CSV", csv, "behandler_statistik.csv", "text/csv")
