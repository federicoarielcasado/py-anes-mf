# PLANIFICACIÓN DE DESARROLLO — PyANES-MF
**Proyecto:** Sistema de Análisis Estructural por Método de las Fuerzas
**Última actualización:** 20 de febrero de 2026
**Versión:** 1.3.0
**Estado:** Motor completo ✓ — 176/176 tests pasando

---

## 📊 ESTADO ACTUAL DEL PROYECTO

### ✅ COMPLETADO (~90%)

#### Modelo estructural y entidades
- [x] Entidades del dominio: `Nudo`, `Barra`, `Material`, `Seccion`, `Vinculo`, `Carga`
- [x] Vínculos: `Empotramiento`, `ApoyoFijo`, `Rodillo`, `Guia`, `ResorteElastico`
- [x] Cargas: `CargaPuntualNudo`, `CargaPuntualBarra`, `CargaDistribuida`, `CargaTermica`, `MovimientoImpuesto`
- [x] Base de datos de materiales (`materials_db.py`) y secciones (`sections_db.py`)
- [x] Serialización JSON completa (`proyecto_serializer.py`)

#### Motor de Método de las Fuerzas
- [x] Cálculo de grado de hiperestaticidad (GH)
- [x] Selección automática de redundantes (`redundantes.py`)
- [x] Generación de estructura fundamental y subestructuras Xi (`subestructuras.py`)
- [x] Cálculo de esfuerzos N(x), V(x), M(x) en subestructuras (`esfuerzos.py`)
- [x] Trabajos virtuales: coeficientes fij y términos independientes e0i (`trabajos_virtuales.py`)
- [x] Efectos térmicos en SECE: `_calcular_e0i_termico()` con ΔT uniforme y gradiente
- [x] Resortes elásticos en SECE: `_agregar_flexibilidad_resortes()` con término 1/k en F[i,i]
- [x] Movimientos impuestos en ecuaciones de compatibilidad
- [x] Resolución del sistema [F]·{X} = -{e0} con `numpy.linalg.solve` (`sece_solver.py`)
- [x] Superposición de resultados: N_final, V_final, M_final
- [x] Reacciones hiperestáticas finales por equilibrio directo
- [x] Verificación de equilibrio global (ΣFx, ΣFy, ΣMz < 1e-6)

#### Interfaz gráfica (PyQt6)
- [x] Ventana principal (`main_window.py`)
- [x] Canvas interactivo con zoom/pan (`structure_canvas.py`)
- [x] Creación de nudos y barras por clic/drag
- [x] Panel de propiedades (`properties_panel.py`)
- [x] Panel de resultados (`results_panel.py`)
- [x] Diálogo de cargas (`carga_dialog.py`)
- [x] Diálogo de redundantes (`redundantes_dialog.py`)
- [x] Undo/Redo (Ctrl+Z / Ctrl+Y) (`undo_redo_manager.py`)

#### Visualización (matplotlib)
- [x] Diagramas M, V, N por barra (`diagramas.py`)
- [x] Visualización de geometría con símbolos de vínculos y cargas (`geometria.py`)
- [x] Deformada elástica con doble integración de M/EI (`deformada.py`)
- [x] Exportación PNG 300 dpi

#### Validación y tests
- [x] **176/176 tests pasando** (unit + integration + domain)
- [x] Casos clásicos GH=1, GH=2, GH=3 validados
- [x] Viga biempotrada, viga continua, pórtico simple
- [x] Cargas térmicas — 20/20 tests unitarios
- [x] Resortes elásticos — 35/35 tests unitarios
- [x] Movimientos impuestos — tests unitarios
- [x] Verificación de equilibrio en todos los casos hiperestáticos

---

### ❌ PENDIENTE (~10%)

- [ ] Exportación de reportes PDF completos (ReportLab)
- [ ] Empaquetado Windows standalone (.exe con PyInstaller)
- [ ] Manual de usuario con capturas de pantalla
- [ ] Documentación técnica generada con Sphinx
- [ ] Tests de integración end-to-end para resortes (análisis completo)
- [ ] Tests de integración end-to-end para deformada

---

## 🎯 ROADMAP — Fase Final (Post-MVP)

El motor de análisis está completo y validado. Los trabajos restantes son de
empaquetado, documentación y experiencia de usuario.

### Tarea 1: Exportación de reportes PDF
**Objetivo:** Generar informe técnico en PDF desde la GUI

**Componentes:**
- Instalar ReportLab: `pip install reportlab`
- Crear `src/ui/export/reporte_pdf.py`
- Incluir: geometría, diagramas M/V/N, tabla de reacciones, tabla de redundantes
- Botón "Exportar PDF" en la toolbar de MainWindow

**Tests:** Verificar que el PDF se genera sin errores y contiene las secciones esperadas

---

### Tarea 2: Empaquetado Windows (.exe)
**Objetivo:** Distribuir la aplicación sin requerir Python instalado

**Pasos:**
```
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico main.py
```

**Verificación:** Ejecutar el .exe en una máquina limpia sin Python

---

### Tarea 3: Manual de usuario + Sphinx
**Objetivo:** Documentación accesible para usuarios no técnicos

**Manual de usuario:**
- Flujo paso a paso: crear modelo → vínculos → cargas → resolver → exportar
- Capturas de pantalla de cada paso
- Glosario de términos estructurales

**Sphinx:**
```
pip install sphinx sphinx-autodoc
sphinx-quickstart docs/sphinx/
```

---

## 🎯 HITOS — Estado Actual

| Hito | Criterio | Estado |
|------|----------|--------|
| **M1:** Esfuerzos N/V/M completos | Tests esfuerzos pasando | ✅ Completado 2026-02-20 |
| **M2:** Trabajos virtuales | Matriz [F] simétrica calculada | ✅ Completado 2026-02-20 |
| **M3:** SECE resuelto | Redundantes correctos en viga biempotrada | ✅ Completado 2026-02-20 |
| **M4:** Motor end-to-end | Caso GH=3 completo sin errores | ✅ Completado 2026-02-20 |
| **M5:** Visualización | Diagramas M/V/N + deformada funcionales | ✅ Completado 2026-02-20 |
| **M6:** Validación completa | 176/176 tests pasando | ✅ Completado 2026-02-20 |
| **M7:** Exportación PDF | Reporte técnico generado | ❌ Pendiente |
| **M8:** Empaquetado | .exe funcional en máquina limpia | ❌ Pendiente |
| **M9:** Manual de usuario | Documentación completa | ❌ Pendiente |

---

## 🔧 COMANDOS ÚTILES

```bash
# Ejecutar todos los tests
py -m pytest -v --tb=short

# Solo resumen (rápido)
py -m pytest --tb=no -q

# Tests de integración
py -m pytest tests/integration/ -v

# Tests unitarios
py -m pytest tests/unit/ -v

# Ejecutar aplicación GUI
py main.py

# Ejecutar ejemplo de viga biempotrada
py ejemplo_viga_biempotrada_gh1.py
```

---

## 📚 DOCUMENTACIÓN DE REFERENCIA

| Documento | Contenido |
|-----------|-----------|
| `CLAUDE.md` | Especificación completa del proyecto, convenciones de signos |
| `docs/ARQUITECTURA_PROYECTO.md` | Estructura de módulos y flujo de ejecución |
| `docs/SISTEMA_COORDENADAS_LOCALES.md` | Convención TERNA (Y+ abajo, rotación horaria+) |
| `docs/SELECCION_REDUNDANTES.md` | Algoritmo de selección automática |
| `docs/teoria/NOTAS_CARGAS_TERMICAS.md` | Efectos térmicos en trabajos virtuales |
| `docs/teoria/NOTAS_RESORTES_ELASTICOS.md` | Vínculos elásticos en SECE |
| `docs/teoria/VISUALIZACION.md` | Módulos de visualización matplotlib |

---

## 🎉 CRITERIO DE ÉXITO FINAL

El proyecto estará **100% completo** cuando:

- ✅ Usuario puede crear estructura en GUI
- ✅ Usuario puede aplicar vínculos y cargas
- ✅ Sistema calcula GH automáticamente
- ✅ Sistema resuelve SECE sin errores
- ✅ Diagramas N, V, M y deformada se muestran correctamente
- ✅ Reacciones coinciden con teoría (error < 1%)
- ✅ 176/176 tests pasan
- ❌ Usuario puede exportar reporte PDF profesional
- ❌ Aplicación funciona como .exe sin instalar Python
- ❌ Manual de usuario disponible

---

*Última actualización: 20 de febrero de 2026 — Versión 1.3.0*
