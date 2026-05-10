# 📋 Requisitos — ERP Nexus

**Versión:** 1.0.0  
**Fecha:** 2026-05-10  
**Estado:** En definición

---

## 🎯 Visión General

ERP Nexus es un framework modular Django para construir sistemas ERP extensibles. El core provee infraestructura (auth, multi-tenant, marketplace) y los módulos son componentes independientes que se instalan bajo demanda.

---

## 📊 Requisitos Funcionales

### **RF-1: Multi-Tenant / Multi-Empresa**
- [ ] Soporte para múltiples empresas en una misma instancia
- [ ] Cada empresa tiene su propio aislamiento de datos
- [ ] Usuarios pueden pertenecer a múltiples empresas con roles diferentes
- [ ] Switch de empresa activa en tiempo de ejecución
- [ ] Contexto `request.active_company` disponible en todo el código

### **RF-2: Sistema de Usuarios y Roles**
- [ ] Autenticación estándar (Usuario/Contraseña)
- [ ] Perfil de usuario extendido (UserProfile)
- [ ] Roles globales (superusuario, staff)
- [ ] Roles por empresa (owner, admin, member, viewer)
- [ ] Permisos granulares por modelo/operación

### **RF-3: Marketplace de Módulos**
- [ ] Catálogo central de módulos disponibles
- [ ] Cada módulo tiene metadata (nombre, versión, dependencias, precio)
- [ ] Registro/instalación de módulos desde catálogo
- [ ] Activación/desactivación de módulos
- [ ] Actualización de versiones
- [ ] Validación de dependencias antes de instalar

### **RF-4: Sistema de Módulos**
- [ ] Los módulos son apps Django independientes
- [ ] Cada módulo reside en su propio repositorio (Git)
- [ ] El core descarga e instala módulos automáticamente
- [ ] Los módulos pueden ser gratuitos o de pago
- [ ] Sistema de licenciamiento por módulo
- [ ] Cada módulo define su propia DB schema (migrations)

### **RF-5: Configuración del Sistema**
- [ ] Configuraciones globales (todas las empresas)
- [ ] Configuraciones por empresa
- [ ] Key-value store simple
- [ ] Valores por defecto configurables
- [ ] Interface de admin para configuraciones

### **RF-6: Chart of Accounts (Plan de Cuentas)**
- [ ] Jerarquía de cuentas contables (padre-hijo)
- [ ] Tipos de cuenta (Activo, Pasivo, Capital, Ingreso, Gasto)
- [ ] Códigos jerárquicos (ej: 1.1.01.001)
- [ ] Asientos de diario
- [ ] Líneas de asiento

### **RF-7: Años Fiscales y Períodos**
- [ ] Definición de años fiscales
- [ ] Períodos contables dentro del año fiscal
- [ ] Cierre de períodos (bloqueo de transacciones)
- [ ] Validación de fechas por período

### **RF-8: Monedas y Tasas de Cambio**
- [ ] Múltiples monedas soportadas
- [ ] Tasas de cambio históricas
- [ ] Conversión automática entre monedas
- [ ] Moneda base configurable

### **RF-9: Dashboard / Analytics**
- [ ] Métricas del sistema (salud, uso)
- [ ] Métricas por empresa
- [ ] Widgets personalizables
- [ ] Gráficos de actividad

### **RF-10: API REST**
- [ ] API versionada (`/api/v1/`)
- [ ] Autenticación JWT
- [ ] Documentación automática (Swagger/OpenAPI)
- [ ] Filtrado, paginación, ordenamiento
- [ ] Rate limiting por módulo

### **RF-11: Admin Django**
- [ ] Admin personalizado (Jazzmin theme)
- [ ]Modelos core registrados
- [ ] Acciones en lote
- [ ] Filtros personalizados
- [ ] Reportes generados desde admin

---

## 🔧 Requisitos No Funcionales

### **RNF-1: Stack Tecnológico**
- **Backend:** Django 5.x + Python 3.12+
- **Base de Datos:** PostgreSQL (producción), SQLite (desarrollo)
- **Cache:** Redis (opcional)
- **API:** Django Ninja (FastAPI-like)
- **Frontend Admin:** Jazzmin + templates Django
- **Despliegue:** Docker + docker-compose

### **RNF-2: Rendimiento**
- Tiempo de respuesta API < 200ms (p95)
- Soporte para 100+ empresas concurrentes
- Cache de consultas frecuentes (Redis)
- Paginación automática en listados (100 items)

### **RNF-3: Seguridad**
- CSRF protection
- SQL injection prevention (ORM)
- XSS protection
- JWT tokens con expiración
- Validación de empresa activa en cada query
- Audit log de cambios sensibles

### **RNF-4: Escalabilidad**
- Arquitectura modular permite agregar módulos sin tocar core
- Base de datos: particionamiento por `company_id`
- Background tasks (Celery opcional)
- Static files en CDN (producción)

### **RNF-5: Mantenibilidad**
- Código siguiendo estándares (ver CODING_STANDARDS.md)
- Tests unitarios >80% cobertura
- Documentación completa por módulo
- Logs estructurados

### **RNF-6: Internacionalización**
- Soporte multi-idioma (i18n)
- Formato de fechas/números por locale
- Monedas y formatos regionales

---

## 🏗️ Alcance (MVP)

### **Incluido en MVP:**
1. Core framework con 6 apps (auth, users, companies, marketplace, config, dashboard)
2. Sistema de módulos básico (instalar/desinstalar desde catálogo)
3. Módulo de ejemplo: `facturacion_ec` (facturación Ecuador)
4. API REST con 10 endpoints principales
5. Admin Django personalizado
6. Docker compose para desarrollo

### **Fuera del Alcance (Post-MVP):**
- Frontend público (SPA/React)
- Múltiples bases de datos (solo PostgreSQL inicial)
- Clustering/horizontal scaling
- Módulos: inventory, sales, accounting, HR
- Integraciones bancarias/pasarelas de pago
- Reportes avanzados (PDF/Excel)

---

## 📈 Criterios de Éxito

| Métrica | Meta | Fecha Límite |
|---------|------|--------------|
| Core funcional | 6 apps instalables | Semana 2 |
| Módulo de ejemplo | facturacion_ec operativo | Semana 4 |
| API endpoints | 20+ endpoints funcionales | Semana 4 |
| Cobertura tests | >70% | Semana 6 |
| Docs completas | README + API docs | Semana 6 |

---

## 🔄 Evolución

**Versión 0.1.x** — Core + Marketplace básico  
**Versión 0.2.x** — Módulo facturacion_ec completo  
**Versión 0.3.x** — Módulo inventory  
**Versión 0.4.x** — Módulo sales  
**Versión 0.5.x** — Docker + despliegue  
**Versión 1.0.0** — Primer release estable

---

**Última actualización:** 2026-05-10
