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
st.write("Tal er afrundet til hele tal med ',' som tusindtalsseparator.")

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
        pva = (nye / behandlinger * 100) if behandlinger != 0 else 0
        
        return pd.Series({
            'Behandlinger': round(behandlinger),
            'Nye': round(nye),
            '1017 samlet': round(sum_1017),
            'Røntgen': round(roentgen),
            'Ultralyd': round(ultralyd),
            'Billeddiagnostik': round(billeddiagnostik),
            'Akupunktur': round(akupunktur),
            'Chokbølge (Antal)': round(chok_antal),
            'Chokbølge (kr.)': round(chok_kr),
            'Total Omsætning': round(total_omsætning),
            'PVA (%)': round(pva)
        })

    # Beregn for hver behandler
    result = df.groupby('Behandler').apply(calculate_stats).reset_index()

    # Beregn TOTAL-rækken
    numeric_only = result.drop(columns='Behandler')
    total_row_values = numeric_only.sum()
    
    # Genberegn PVA for totalen korrekt før afrunding
    if total_row_values['Behandlinger'] != 0:
        total_pva = (total_row_values['Nye'] / total_row_values['Behandlinger'] * 100)
    else:
        total_pva = 0
        
    total_row = total_row_values.to_dict()
    total_row['Behandler'] = 'TOTAL'
    total_row['PVA (%)'] = round(total_pva)
    
    # Saml resultatet
    result = pd.concat([result, pd.DataFrame([total_row])], ignore_index=True)

    # Tving alle talkolonner til at være faktiske taltyper (vigtigt for formatering)
    num_cols = result.columns.drop('Behandler')
    for col in num_cols:
        result[col] = pd.to_numeric(result[col])

    # Vis tabellen
    # Vi bruger format="{:,d}" eller bare "d" for heltal. 
    # Streamlit NumberColumn bruger d3-format, så ",d" er tusindtal med komma for heltal.
    st.subheader("Opgørelse pr. behandler")
    st.dataframe(
        result,
        use_container_width=True,
        column_config={
            col: st.column_config.NumberColumn(format=",d") for col in num_cols
        }
    )

    # Download
    csv = result.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.download_button("Download resultat som CSV", csv, "behandler_statistik.csv", "text/csv")
