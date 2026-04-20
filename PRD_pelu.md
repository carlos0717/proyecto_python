# PRD — Peluquería Estilo

**Alumno:** [Tu nombre]
**Fecha:** 11 de abril de 2026
**Tipo de proyecto:** Web App
**Estado:** 🟡 En planeación

---

## 1. Descripción del Proyecto

Peluquería Estilo es una aplicación web que permite gestionar los ingresos, egresos, servicios, productos y empleados de una peluquería. El sistema facilita el control diario y mensual del negocio mediante registros simples y un dashboard interactivo para la toma de decisiones.

---

## 2. El Problema

**¿Quién tiene el problema?**  
Dueños de peluquerías con pocos conocimientos técnicos y pequeños equipos de trabajo.

**¿Cuál es el problema?**  
Llevar el control de ingresos y egresos de forma manual (cuadernos o Excel) es desordenado, propenso a errores y dificulta el análisis del negocio.

**¿Qué hacen hoy sin este proyecto?**  
Registran información en cuadernos físicos o en hojas de Excel sin automatización ni análisis claro.

---

## 3. Usuario Principal

- **¿Quién es?** Dueño o administrador de una peluquería con 1 a 3 empleados.
- **¿Qué quiere lograr?** Controlar ingresos, egresos y rendimiento del negocio de forma clara y rápida.
- **¿Qué le frustra?** La falta de organización, errores manuales y dificultad para analizar los datos.

---

## 4. Funcionalidades

### ✅ Incluidas en el proyecto (MVP)

1. Registro de ingresos y egresos (servicios y productos)
   - Criterio de éxito: Al registrar una operación, aparece en la lista y se refleja en el total del día.

2. Gestión de empleados
   - Criterio de éxito: Se pueden crear, editar, desactivar empleados y asignar roles correctamente.

3. Autenticación y roles (administrador, gerente, empleado)
   - Criterio de éxito: Cada usuario accede solo a las funcionalidades permitidas según su rol.

4. Dashboard con reportes (diario y mensual)
   - Criterio de éxito: Se visualizan correctamente los totales y filtros por fecha sin errores.

---

### ⏸️ Para después (fuera del MVP)

- Reservas en línea por clientes
- Pagos electrónicos
- Integración con SUNAT
- Verificación por correo electrónico
- Notificaciones automáticas

---

### ❌ Fuera del alcance

- Aplicación móvil
- Sistema de pagos en línea en esta versión
- Integraciones externas complejas (SUNAT, APIs externas)

---

## 5. Stack Técnico

- **Lenguaje:** Python
- **Framework:** Django
- **Base de datos:** SQLite (inicial) / PostgreSQL (escalable)
- **Frontend:** HTML + CSS (Django Templates + HTMX, Responsive)
- **Autenticación:** Django Auth con sistema de roles

---

## 6. Definición de MVP Terminado

El proyecto está listo cuando:
- [ ] Se pueden registrar ingresos y egresos sin errores
- [ ] Existen al menos 2 roles funcionando correctamente
- [ ] El dashboard muestra datos reales filtrables por fecha

---

## 7. Cómo saber si el proyecto fue exitoso

- El sistema permite registrar correctamente operaciones diarias sin errores
- Se puede visualizar un dashboard útil para la toma de decisiones del negocio

---

## 8. Riesgos y Dudas

| Riesgo o duda                     | ¿Qué podrías hacer?                          |
|----------------------------------|----------------------------------------------|
| Manejo de roles y permisos       | Usar sistema de grupos de Django             |
| Complejidad del dashboard        | Empezar con datos simples y luego mejorar    |
| Uso de HTMX                      | Implementar primero sin HTMX, luego agregar  |
| Diseño de base de datos          | Mantener modelos simples y normalizados      |