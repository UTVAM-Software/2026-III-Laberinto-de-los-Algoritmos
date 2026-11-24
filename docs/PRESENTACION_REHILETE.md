# Presentación en El Rehilete

- El logo original está en el acceso, el inicio, la barra de navegación y la proyección.
- «Pantalla completa» amplía la pestaña actual y conserva los controles. Pulsa el mismo botón o Esc para salir. Si el navegador no admite pantalla completa, se utiliza una vista ampliada reversible.
- En Dinámico, «Proyectar en otra pestaña» abre deliberadamente una vista de solo lectura. Mueve esa pestaña a la segunda pantalla; el guía responde y confirma los movimientos desde la pestaña original. No compartas el enlace de proyección fuera del evento.
- Las proyecciones conservan su vencimiento de ocho horas desde la creación de la partida.

## Comprobación antes del concurso

1. Inicia el servidor y accede con una cuenta existente.
2. Confirma que se ve el logo; recarga con Ctrl+F5 si el navegador conserva estilos antiguos.
3. Prueba Individual: inicia, responde, muestra el resultado y reintenta.
4. Prueba Dinámico: abre la proyección, vuelve al control original, inicia el tablero y confirma la meta. La segunda pestaña debe mostrar las mismas preguntas sin botones de respuesta.
5. Prueba «Pantalla completa» y Esc. Comprueba también en el equipo y proyector del concurso.
6. Conserva un respaldo de PostgreSQL antes del evento. No ejecutes seed_initial en una base ya preparada para actualizar estos archivos.

## Verificación de esta entrega

Base: main c5f303b. Pasaron 88 pruebas Django con SQLite de prueba, las 4 pruebas de controles de pantalla (`node --test tests/screen.test.cjs`), la compilación de 36 plantillas y collectstatic. No hay migraciones ni cambios en la base de datos. La inspección visual interactiva quedó pendiente porque el navegador disponible no puede acceder al servidor local del entorno; debe comprobarse en el equipo de la presentación. Estas pruebas no sustituyen una prueba real con PostgreSQL y el proyector.

## Logo y música

El logo utiliza un PNG transparente. Activa «Sonido: apagado» dentro de la partida para oír una melodía breve al ganar o perder. El sonido comienza apagado en cada página; al apagarlo se detienen las notas. Salir voluntariamente no reproduce música de derrota. Las melodías se generan localmente y no necesitan internet. La proyección permanece silenciosa para evitar audio duplicado.
