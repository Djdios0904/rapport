import streamlit as st
import pandas as pd
import io

# Hjælpefunktioner til datarensning
def clean_antal(val):
    s = str(val).strip()
    if s == '03.feb': return 3.0
    s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

def clean_beloeb(val):
    if pd.isna(val): return 0.0
    # Fjerner ' kr.', tusindtalsseparator (.) og ændrer komma til punktum
    s = str(val).replace(' kr.', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

# App layout
st.set_page_config(page_title="Behandler Statistik", layout="wide")
st.title("📊 Behandler Produktions-Opgørelse")
st.write("Upload din CSV-fil for at få beregnet statistikken med de nye 1017 og Chokbølge-antal.")

uploaded_file = st.file_uploader("Vælg CSV-fil", type="csv")

if uploaded_file is not None:
    # Læs filen (prøver UTF-8, ellers Latin-1 som ofte bruges i DK exports)
    try:
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=';', encoding='latin-1')
    
    # Rens data
    df['Antal_clean'] = df['Antal'].apply(clean_antal)
    df['Beløb_clean'] = df['Beløb'].apply(clean_beloeb)
    df['Kode'] = df['Kode'].astype(str).str.strip()

    # Definitioner af kodelister
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
        
        # Chokbølge - både antal og beløb
        chok_rows = group[group['Kode'].isin(codes_chokboelge)]
        chok_antal = chok_rows['Antal_clean'].sum()
        chok_kr = chok_rows['Beløb_clean'].sum()
        
        pva = (nye / behandlinger * 100) if behandlinger != 0 else 0
        
        return pd.Series({
            'Behandlinger': behandlinger,
            'Nye': nye,
            '1017 samlet': sum_1017,
            'Røntgen': roentgen,
            'Ultralyd': ultralyd,
            'Billeddiagnostik': billeddiagnostik,
            'Akupunktur': akupunktur,
            'Chokbølge (Antal)': chok_antal,
            'Chokbølge (kr.)': chok_kr,
            'PVA (%)': round(pva, 2)
        })

    # Lav beregningen
    result = df.groupby('Behandler').apply(calculate_stats).reset_index()

    # Vis tabellen
    st.subheader("Opgørelse pr. behandler")
    st.dataframe(result, use_container_width=True)

    # Download link
    csv = result.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.download_button(
        label="Download resultat som CSV",
        data=csv,
        file_name="behandler_statistik_opdateret.csv",
        mime="text/csv",
    )