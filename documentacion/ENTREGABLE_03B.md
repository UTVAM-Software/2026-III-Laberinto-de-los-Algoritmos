# Entregable 03-B: autenticación, CRUD y control de accesos

## Implementación

El Laberinto de los Algoritmos organiza sus funciones en las aplicaciones `cuentas`, `escuela`, `preguntas`, `juego`, `progreso` y `administracion`. Conservamos el modelo de usuario `core.User`, basado en `AbstractUser`, y PostgreSQL como base de datos de la aplicación.

### Autenticación

Utilizamos `LoginView` y `LogoutView` de Django. Las rutas están en `cuentas/urls.py`; las pantallas de acceso y registro se encuentran en `cuentas/templates/cuentas/`. Configuramos `LOGIN_URL`, `LOGIN_REDIRECT_URL` y `LOGOUT_REDIRECT_URL` en `config/settings.py`. El cierre de sesión utiliza POST y protección CSRF.

### CRUD y listado

Implementamos un módulo propio en `/gestion/`, accesible desde el enlace Administración de la cuenta administradora. Sus pantallas permiten crear, listar, consultar, actualizar y eliminar registros de las siguientes entidades:

| Entidad | Ruta de listado |
| --- | --- |
| Usuarios | `/gestion/usuarios/` |
| Roles y grupos de permisos | `/gestion/roles/` |
| Permisos | `/gestion/permisos/` |
| Materias | `/gestion/materias/` |
| Categorías | `/gestion/categorias/` |
| Grupos escolares | `/gestion/grupos/` |
| Alumnos | `/gestion/alumnos/` |
| Preguntas | `/gestion/preguntas/` |
| Partidas | `/gestion/partidas/` |
| Preguntas de partida | `/gestion/respuestas/` |
| Aprendizajes logrados | `/gestion/aprendizajes/` |
| Mundos desbloqueados | `/gestion/desbloqueos/` |

Cada listado incorpora búsqueda y paginación. El catálogo de entidades y campos editables es explícito: no se resuelven modelos arbitrarios a partir de la URL. Las operaciones usan formularios de Django con validación de campos y relaciones. Los identificadores de seguridad y las contraseñas almacenadas no se muestran en las pantallas de detalle.

Los profesores conservan sus pantallas de grupos escolares, alumnos y preguntas con alcance limitado a sus registros. El buscador de alumnos combina nombre o alias y categoría sin ampliar ese alcance.

### Administración de Django Auth

Desde nuestras interfaces administramos `core.User`, `auth.Group` y `auth.Permission`, sin depender exclusivamente de `/admin/`. En el formulario de usuario asignamos grupos y permisos individuales; en el formulario de grupo configuramos sus permisos. Las cuentas nuevas utilizan `UserCreationForm`. Las nuevas contraseñas se validan y se guardan mediante `set_password`; los campos vacíos al editar conservan la contraseña anterior. No permitimos que el administrador elimine su propia cuenta, se desactive o se quite su propio acceso administrativo, ni que se desactive al último administrador activo desde estos formularios.

### Control de acceso

Las vistas administrativas heredan de `AdminAccess`, que combina `LoginRequiredMixin` y `PermissionRequiredMixin`, exige un superusuario activo y determina el permiso específico de consulta, alta, cambio o eliminación. Un profesor, alumno o visitante recibe HTTP 403 aunque escriba la URL o envíe un POST directamente.

Las vistas escolares usan `SchoolPermission` y declaran `permission_required`. Las consultas de detalle, edición y eliminación reutilizan funciones de alcance como `students_for` y `classrooms_for`. El acceso al juego utiliza `AttemptAccessMixin`, `attempts_for` y la comprobación adicional de quién puede controlar una partida.

Las eliminaciones administrativas se confirman mediante POST con CSRF; el GET únicamente muestra la confirmación. La confirmación informa los registros que se eliminarían en cascada. Las relaciones `PROTECT` y `RESTRICT` impiden borrar registros referenciados y presentan un mensaje en vez de producir un error del servidor. Las pantallas escolares conservan sus reglas de archivado y retiro cuando existe historial.

La pantalla de proyección es una excepción pública deliberada: utiliza un token aleatorio, caduca después de ocho horas y permite únicamente observar la información prevista por el juego. No concede acceso al módulo administrativo ni a acciones de control.

### Métodos y propiedades

Los modelos incluyen representaciones `__str__`, validaciones `clean()` y la propiedad de solo lectura `Question.options`. La validación de categorías comprueba las reglas de tiempo y número de rutas; la de preguntas evita opciones repetidas.

## Validación automatizada

Se ejecutaron las 79 pruebas existentes y las nueve pruebas nuevas de administración. Las pruebas nuevas recorren las interfaces de las 12 entidades y prueban creación, actualización y eliminación, almacenamiento de contraseñas, asignación de grupos y permisos, prohibición de acceso a visitantes/profesores/alumnos, CSRF, protección de relaciones, restricciones sobre la propia cuenta, identificadores inválidos y búsqueda de alumnos limitada al profesor.

Entorno de verificación: Python 3.12, Django 5.2.18 y SQLite habilitado exclusivamente mediante `LAB_TEST_SQLITE=1`. Esta ejecución no sustituye la comprobación del entorno PostgreSQL de cada integrante. `manage.py check` no detectó problemas y `makemigrations --check --dry-run` no detectó cambios de esquema.

## Comprobación local con PostgreSQL

Desde la carpeta del proyecto, con `.env` ya configurado y el entorno instalado:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test --noinput
.\.venv\Scripts\python.exe manage.py runserver
```

Si no existe una cuenta administradora, crearla sin compartir su contraseña:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Iniciar sesión en `http://127.0.0.1:8000/cuenta/login/` y entrar a `http://127.0.0.1:8000/gestion/`. No se requieren migraciones nuevas para este módulo.

## Guion de demostración

1. Iniciar sesión como administrador y abrir Administración.
2. Crear una materia de prueba, consultarla, editarla y eliminarla.
3. Crear un permiso de prueba asociado a un tipo de contenido; crear un rol y asignarle ese permiso.
4. Crear un usuario con contraseña propia, asignarle el rol y un permiso individual. Consultar y editar la cuenta.
5. Mostrar los listados y formularios de las demás entidades. Usar datos ficticios para las operaciones que modifiquen historial.
6. Intentar eliminar una categoría con preguntas relacionadas y comprobar el bloqueo por dependencia.
7. Cerrar sesión; intentar abrir `/gestion/usuarios/` y comprobar el rechazo.
8. Iniciar sesión como profesor, intentar la misma URL y comprobar el rechazo.
9. Abrir Alumnos, buscar por nombre y categoría y comprobar que solo aparecen alumnos del profesor correspondiente.
10. Comprobar que las operaciones de modificación requieren POST y CSRF mediante la suite de pruebas.

## Integración y entrega

Los cambios deben revisarse, aprobarse y fusionarse mediante Pull Request hacia `main` antes de entregar. Este documento describe la implementación; el estado de aprobación e integración se comprueba en GitHub.

Repositorio del equipo: https://github.com/UTVAM-Software/2026-III-Laberinto-de-los-Algoritmos

La guía solicita entregar el enlace del repositorio en Google Classroom, escribir los nombres completos de los integrantes comenzando por apellidos en el comentario privado y marcar la actividad como entregada. La entrega corresponde a un integrante en representación del equipo.
