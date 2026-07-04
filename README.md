# Twitter-Bot

## English

### Description
A Twitter/X bot with a small, modern desktop GUI (Tkinter + ttkbootstrap). It uses Tweepy's v2 `Client` to post, delete, search, like, retweet and manage follows. Built with an MVC layout: `model.py` (X API access), `view.py` (GUI), `controller.py` (wiring, background threads).

### Features
- Compose a tweet with a live character counter (280) and an optional image attachment (with thumbnail preview).
- View your recent tweets and delete any of them.
- Search recent tweets by keyword; like or retweet results directly from the list.
- Bulk-like tweets by keyword, with per-tweet progress and error reporting (one failure doesn't abort the batch).
- Follow / unfollow a specific user by handle.
- Light/dark theme toggle.
- Optional credential persistence via your OS keychain (`keyring`), or a local `.env` file for development. Secret fields are always masked in the UI.
- All API calls run on a background thread so the UI never freezes.

### A note on X API access tiers
This bot targets the X API v2 user-context endpoints. The **Free** tier only allows posting/deleting/liking your own content; **search, timelines, and follow management require at least the Basic tier**. If an action fails with an access-tier error, the app will tell you clearly instead of crashing — that's an X API limitation, not a bug in this project.

### Requirements
- Python 3.10+
- See `requirements.txt` (Tweepy, ttkbootstrap, python-dotenv, keyring, Pillow)

### Installation
```sh
git clone https://github.com/yourusername/twitter-bot.git
cd twitter-bot
pip install -r requirements.txt
```

### Usage
```sh
python main.py
```
Enter your X API v1.1 user-context credentials (Consumer Key/Secret, Access Token/Secret) in the login screen, or copy `.env.example` to `.env` and fill it in beforehand. Tick "Remember credentials on this device" to save them to your OS keychain for next time.

### Tests
```sh
python -m unittest discover -s tests
```

### License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.



## Español

### Descripción
Un bot para Twitter/X con una interfaz de escritorio pequeña y moderna (Tkinter + ttkbootstrap). Usa el `Client` v2 de Tweepy para publicar, borrar, buscar, dar me gusta, retwittear y gestionar follows. Sigue un esquema MVC: `model.py` (acceso a la API de X), `view.py` (interfaz), `controller.py` (conexión y hilos en segundo plano).

### Características
- Redactar un tweet con contador de caracteres en vivo (280) y adjuntar una imagen opcional (con vista previa).
- Ver tus tweets recientes y eliminar cualquiera de ellos.
- Buscar tweets recientes por palabra clave; dar me gusta o retwittear directamente desde la lista de resultados.
- Dar me gusta masivo por palabra clave, con progreso y errores por tweet (un fallo no aborta el resto del lote).
- Seguir / dejar de seguir a un usuario específico por su @usuario.
- Cambio de tema claro/oscuro.
- Guardado opcional de credenciales en el llavero del sistema operativo (`keyring`), o mediante un archivo `.env` local para desarrollo. Los campos secretos siempre aparecen enmascarados en la interfaz.
- Todas las llamadas a la API corren en un hilo en segundo plano para que la interfaz nunca se congele.

### Nota sobre los niveles de acceso de la API de X
Este bot usa los endpoints v2 de la API de X en contexto de usuario. El nivel **Free** solo permite publicar/borrar/dar me gusta a tu propio contenido; **la búsqueda, las líneas de tiempo y la gestión de follows requieren al menos el nivel Basic**. Si una acción falla por nivel de acceso insuficiente, la aplicación lo indica claramente en vez de fallar sin explicación — es una limitación de la API de X, no un bug del proyecto.

### Requisitos
- Python 3.10+
- Ver `requirements.txt` (Tweepy, ttkbootstrap, python-dotenv, keyring, Pillow)

### Instalación
```sh
git clone https://github.com/yourusername/twitter-bot.git
cd twitter-bot
pip install -r requirements.txt
```

### Uso
```sh
python main.py
```
Ingresa tus credenciales de contexto de usuario de la API v1.1 de X (Consumer Key/Secret, Access Token/Secret) en la pantalla de login, o copia `.env.example` a `.env` y complétalo antes. Marca "Recordar credenciales en este equipo" para guardarlas en el llavero del sistema operativo.

### Tests
```sh
python -m unittest discover -s tests
```

### Licencia
Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
