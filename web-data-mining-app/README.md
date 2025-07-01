# Aplicación Web de Minería de Datos para el Sector Salud

Una aplicación web moderna y robusta para la gestión, búsqueda, almacenamiento y visualización de contactos y oportunidades comerciales en el sector salud. Incluye funcionalidades tipo CRM, seguimiento post-venta, y un panel Kanban para gestión de oportunidades.

## 🚀 Características Principales

- **Búsqueda Inteligente**: Scraping automatizado de contactos con IA
- **CRM Completo**: Panel Kanban, métricas, filtros avanzados
- **Gestión de Tareas**: Asignación y seguimiento por usuario
- **Sistema de Actividades**: Historial completo de interacciones
- **Base de Datos**: PostgreSQL con modelos optimizados
- **Interfaz Moderna**: Diseño responsive con Bootstrap 5
- **Autenticación**: Sistema JWT con Google OAuth

## 📁 Estructura del Proyecto

```
web-data-mining-app/
├── src/
│   ├── app.py                    # Aplicación principal Flask
│   ├── config.py                 # Configuración de la aplicación
│   ├── auto_search.py            # Búsqueda automática con IA
│   ├── models/
│   │   ├── database.py           # Modelos SQLAlchemy
│   │   └── search_model.py       # Modelo de búsqueda
│   ├── routes/
│   │   ├── auth_routes.py        # Rutas de autenticación
│   │   ├── auto_search_routes.py # Rutas de búsqueda inteligente
│   │   ├── clients_routes.py     # Rutas de clientes guardados
│   │   ├── crm_routes.py         # Rutas del CRM y Kanban
│   │   ├── followup_routes.py    # Rutas de seguimiento
│   │   └── search_routes.py      # Rutas de búsqueda básica
│   ├── services/
│   │   ├── data_mining_service.py # Servicio de minería de datos
│   │   └── validator.py          # Validaciones
│   └── templates/
│       ├── *.html                # Templates Jinja2
├── requirements.txt              # Dependencias del proyecto
├── run.py                        # Script principal de ejecución
└── README.md                     # Este archivo
```

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- PostgreSQL 12+
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <repository-url>
   cd web-data-mining-app
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar base de datos:**
   - Crear una base de datos PostgreSQL
   - Configurar las variables de entorno en `src/config.py`

4. **Ejecutar la aplicación:**
   ```bash
   python run.py
   ```

## 🖥️ Uso de la Aplicación

### Acceso
- Abrir navegador en: `http://127.0.0.1:5000`
- Usar las credenciales por defecto o registrarse

### Funcionalidades Principales

#### 🔍 Búsqueda de Contactos
- **Búsqueda básica**: Términos simples para encontrar contactos
- **Búsqueda inteligente**: IA que sugiere términos y filtros optimizados
- **Scraping automatizado**: Extracción de datos de múltiples fuentes

#### 👥 Gestión de Clientes
- **Clientes guardados**: Lista filtrable de contactos almacenados
- **Deduplicación automática**: Evita contactos duplicados
- **Limpieza de datos**: Normalización automática de información

#### 🎯 CRM y Oportunidades
- **Panel Kanban**: Visualización de oportunidades por estado
- **Estados**: Nuevo, Seguimiento, Oportunidad, Cerrado, Obsoleto
- **Métricas**: Dashboard con estadísticas y gráficos
- **Filtros avanzados**: Por nombre, rubro, representante, etc.

#### ✅ Gestión de Tareas
- **Asignación**: Tareas por usuario con fechas de vencimiento
- **Prioridades**: Alta, Media, Baja
- **Tipos**: General, Llamada, Email, Reunión, Seguimiento
- **Seguimiento**: Comentarios y resultados de tareas completadas

#### 📊 Panel de Estadísticas
- **Métricas de búsqueda**: Contactos encontrados, calidad promedio
- **Estadísticas CRM**: Oportunidades por estado, valor estimado
- **Gráficos interactivos**: Visualización de tendencias
- **Análisis de rendimiento**: Métricas de conversión

## 🗄️ Base de Datos

### Modelos Principales
- **Contact**: Información de contactos
- **Opportunity**: Oportunidades comerciales
- **Task**: Tareas asignadas
- **Activity**: Historial de actividades
- **User**: Usuarios del sistema

## 🔧 Configuración Avanzada

### Variables de Entorno
Configurar en `src/config.py`:
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para JWT
- `GOOGLE_CLIENT_ID`: Para OAuth (opcional)

### Personalización
- **Filtros Jinja2**: Personalizados para fechas y ordenamiento
- **Validaciones**: Sistema robusto de validación de datos
- **Logging**: Sistema de logs para debugging

## 🤝 Contribución

1. Fork del proyecto
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
- Input search criteria to find potential clients.
- Retrieve and display contact information, including names, emails, phone numbers, and locations.
- Utilize a clean and intuitive user interface for seamless interaction.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.