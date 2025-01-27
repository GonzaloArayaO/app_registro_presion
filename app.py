import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz

st.set_page_config(
    page_title='Registro Presión',
    page_icon='assets/app_icon.png'
    )

# Configurar credenciales de Google Sheets
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(credentials)

# Abrir la hoja de Google Sheets
sheet = client.open("registro_presion").sheet1

# Función para mostrar datos
def obtener_datos():
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df['Fecha'] = pd.to_datetime(df['Fecha'], format="%d-%m-%Y")
    return df

# Interfaz de Registro
st.write("# Registro Presión Arterial")

# Tabs
tab1, tab2, tab3 = st.tabs(["Registro de Presión", "Visualización", "Tabla de registros"])

with tab1:
    st.write('#### Formulario:')
    fecha = st.date_input("Fecha", key='fecha_input')

    col1, col2, col3 = st.columns(3)
    with col1:
        alta = st.number_input("Presión Alta", min_value=0, step=1, format="%d", key='alta_input')
    with col2:
        baja = st.number_input("Presión Baja", min_value=0, step=1, format="%d", key='baja_input')
    with col3:
        pulso = st.number_input("Pulsaciones", min_value=0, step=1, format="%d", key='pulso_input')

    hora_utc = datetime.utcnow()
    zona_horaria = pytz.timezone('America/Santiago')
    hora_local = hora_utc.astimezone(zona_horaria)
    hora_formateada = hora_local.strftime("%H:%M")

    # Botón registrar
    if st.button("Registrar", key="registrar_button"):
        # Convertir la fecha al formato Día, Mes, Año
        fecha_formateada = fecha.strftime("%d-%m-%Y")
        # Validar que todos los valores estén completos
        if not fecha_formateada or alta == 0 or baja == 0 or pulso == 0:
            st.error("Todos los valores son obligatorios. Por favor, complete todos los campos.")
        else:
            data = [str(fecha_formateada), hora_formateada, alta, baja, pulso]
            sheet.append_row(data)
            st.success("Datos registrados correctamente")

with tab2:
    df = obtener_datos()
    df['Fecha'] = df['Fecha'].dt.strftime('%d-%m-%Y')
    if not df.empty:
        # Agrupar por fecha y calcular el promedio de columnas numéricas
        df_avg = df.groupby('Fecha', as_index=False)[['Alta', 'Baja', 'Pulso']].mean()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_avg['Fecha'],
            y=df_avg['Alta'],
            mode='lines+markers',
            name='Alta',
            line=dict(color='#228B22', width=2),
            marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=df_avg['Fecha'],
            y=df_avg['Baja'],
            mode='lines+markers',
            name='Baja',
            line=dict(color='#FF8C00', width=2),
            marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=df_avg['Fecha'],
            y=df_avg['Pulso'],
            mode='lines+markers',
            name='Pulso',
            line=dict(color='#1E90FF', width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title="Promedio diario de Presión Alta, Baja y Pulsaciones",
            xaxis=dict(
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                tickangle=270
            ),
            yaxis=dict(
                title="Valores Promedio",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                rangemode='tozero'
            ),
            legend_title=dict(
                text="Variables (promedio)",
                font=dict(color="black")
            ),
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos disponibles para visualizar.")

with tab3:
    st.write('''#### Tabla registros\n- Ordenados del más reciente al más antiguo.''')
    df = obtener_datos()
    if not df.empty:
        df['Fecha'] = df['Fecha'].dt.strftime('%d-%m-%Y')
        df = df.iloc[::-1].reset_index(drop=True)
        # Aplicar estilos al DataFrame
        styled_df = df.style.set_table_styles([
            {'selector': 'thead th', 'props': [('background-color', '#1F618D'), 
                                               ('color', 'white'), 
                                               ('font-weight', 'bold')]},
            {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]},  # Filas pares
            {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', 'white')]}  # Filas impares
        ]).set_properties(**{'text-align': 'center',
                             'font-size': '14px'})

        # Mostrar tabla estilizada
        st.write(styled_df.to_html(), unsafe_allow_html=True)
    else:
        st.warning('No hay datos disponibles.')