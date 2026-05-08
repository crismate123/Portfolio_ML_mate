import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json

# 1. Autenticación a Firestore
if not firebase_admin._apps:
    # Verificamos si estamos en la nube (Streamlit Cloud) buscando los "secrets"
    if "firebase_credentials" in st.secrets:
        # MODO NUBE
        key_dict = json.loads(st.secrets["firebase_credentials"])
        
        # --- SOLUCIÓN AL ERROR DE CREDENCIALES ---
        # Aseguramos que los saltos de línea de la llave privada se lean correctamente
        if 'private_key' in key_dict:
            key_dict['private_key'] = key_dict['private_key'].replace('\\n', '\n')
        
        cred = credentials.Certificate(key_dict)
    else:
        # MODO LOCAL
        # Reemplaza con la ruta de tu compu para seguir probando localmente
        cred = credentials.Certificate(r'C:\Users\cm180\Downloads\Proyecto_S_DS\TU_ARCHIVO_JSON_CORRECTO.json')
    
    firebase_admin.initialize_app(cred)

db = firestore.client()
# 2. Función para leer los datos desde el arranque
# Usamos @st.cache_data para que la función se ejecute solo una vez y no cada vez que interactuamos con la app
@st.cache_data
def load_data():
    # Hacemos referencia a la colección 'movies' (o el nombre que le hayas puesto)
    movies_ref = db.collection('movies')
    docs = movies_ref.stream()
    
    # Convertimos los documentos de Firestore a una lista de diccionarios
    data = []
    for doc in docs:
        data.append(doc.to_dict())
        
    # Retornamos los datos como un DataFrame de Pandas
    return pd.DataFrame(data)

# Ejecutamos la función para tener el dataset base disponible
df_movies = load_data()

# Para comprobar que funciona, mostraremos un título y un mensaje temporal
st.title("Netflix app - Mi Dashboard de Películas")
st.write("¡Datos cargados exitosamente de Firestore!")
# st.dataframe(df_movies) # Descomenta esta línea si quieres ver la tabla completa por ahora


# --- SIDEBAR (Barra Lateral) ---

# 1. Checkbox para mostrar todos los filmes
mostrar_todos = st.sidebar.checkbox('Mostrar todos los filmes')

# 2. Búsqueda por título
titulo_busqueda = st.sidebar.text_input('Titulo del filme :')
btn_buscar = st.sidebar.button('Buscar filmes')

# 3. Filtro por director
# Extraemos los directores únicos del DataFrame y los ordenamos (opcional, pero se ve mejor)
lista_directores = df_movies['director'].dropna().unique()
director_seleccionado = st.sidebar.selectbox('Seleccionar Director', lista_directores)
btn_filtrar_director = st.sidebar.button('Filtrar director')


# --- ÁREA PRINCIPAL (Resultados) ---

# Evaluamos qué opción eligió el usuario:

if mostrar_todos:
    st.header("Todos los filmes")
    st.dataframe(df_movies)

elif btn_buscar:
    # Búsqueda que contiene el texto y no distingue mayúsculas/minúsculas (case=False)
    filmes_encontrados = df_movies[df_movies['name'].str.contains(titulo_busqueda, case=False, na=False)]
    
    st.header("Netflix app")
    st.write(f"Total filmes mostrados : {len(filmes_encontrados)}")
    st.dataframe(filmes_encontrados)

elif btn_filtrar_director:
    # Filtrado exacto por la columna 'director'
    filmes_director = df_movies[df_movies['director'] == director_seleccionado]
    
    st.header("Netflix app")
    st.write(f"Total filmes : {len(filmes_director)}")
    st.dataframe(filmes_director)

else:
    # Mensaje por defecto cuando no hay nada seleccionado
    st.info("Utiliza el menú lateral para buscar o filtrar películas.")

# --- FORMULARIO PARA NUEVO FILME ---
st.sidebar.markdown("---") # Una línea divisoria
st.sidebar.header("Nuevo filme")

# Campos del formulario
new_name = st.sidebar.text_input("Name:")
# Para Company, Director y Genre, puedes usar selectbox con las opciones existentes 
# o text_input para algo totalmente nuevo. Aquí usamos selectbox para seguir el ejemplo:
new_company = st.sidebar.selectbox("Company", df_movies['company'].unique())
new_director = st.sidebar.selectbox("Director ", df_movies['director'].unique())
new_genre = st.sidebar.selectbox("Genre", df_movies['genre'].unique())

btn_crear = st.sidebar.button("Crear nuevo filme")

if btn_crear:
    if new_name:
        # 1. Crear el diccionario con los datos
        new_doc = {
            "name": new_name,
            "company": new_company,
            "director": new_director,
            "genre": new_genre
        }
        # 2. Insertar en Firestore
        db.collection('movies').add(new_doc)
        
        st.sidebar.success(f"¡Filme '{new_name}' insertado correctamente!")
        # Opcional: Limpiar el caché para ver el cambio de inmediato
        st.cache_data.clear()
    else:
        st.sidebar.error("Por favor, ingresa el nombre del filme.")

