# PLANIFICACIÓN DE DESARROLLO - PyANES-MF
**Proyecto:** Sistema de Análisis Estructural por Método de las Fuerzas
**Fecha:** 11 de febrero de 2025
**Estado Actual:** Motor de reacciones isostáticas funcionando ✓

---

## 📊 ESTADO ACTUAL DEL PROYECTO

### ✅ COMPLETADO (30%)
- [x] Estructura básica del proyecto (MVC)
- [x] Entidades del dominio (Nudo, Barra, Material, Sección, Vínculo, Carga)
- [x] Base de datos de materiales y secciones
- [x] Interfaz gráfica completa (PyQt6)
  - Canvas interactivo con zoom/pan
  - Creación de nudos y barras por clic
  - Panel de propiedades
  - Panel de resultados
  - Diálogos de cargas
- [x] Cálculo de grado de hiperestaticidad (GH)
- [x] Selección de redundantes (básico)
- [x] **Resolución de reacciones isostáticas (CRÍTICO)** ✓
  - Fórmula correcta con TERNA
  - Validación con test_reacciones_simple.py
- [x] **Visualización de reacciones como diagrama de cuerpo libre** ✓
  - Flechas verdes para Rx, Ry
  - Arcos para momentos Mz
  - Etiquetas con valores

### 🔨 EN PROGRESO (40%)
- [ ] Cálculo de esfuerzos internos N(x), V(x), M(x)
  - Estructura creada en `esfuerzos.py`
  - Falta implementación completa

### ❌ PENDIENTE (30%)
- [ ] Trabajos virtuales (fij, e0i)
- [ ] Solver SECE
- [ ] Superposición de resultados
- [ ] Visualización de diagramas de esfuerzos
- [ ] Deformadas
- [ ] Exportación de resultados
- [ ] Suite completa de validación

---

## 🎯 PLAN DE DESARROLLO (8 SEMANAS)

### **FASE 1: MOTOR DE ESFUERZOS (Semanas 1-2)**
**Objetivo:** Calcular N(x), V(x), M(x) para cualquier estructura isostática

#### Semana 1: Esfuerzos en barras simples
**Archivo:** `src/domain/mechanics/esfuerzos.py`

**Tareas:**
1. **Implementar cálculo de N(x) para barra con cargas axiales**
   ```python
   def calcular_N_barra(barra, reacciones, cargas):
       # N constante en cada tramo
       # Cambios en cargas puntuales axiales
   ```

2. **Implementar cálculo de V(x) para barra con cargas transversales**
   ```python
   def calcular_V_barra(barra, reacciones, cargas):
       # V constante entre cargas puntuales
       # V varía linealmente con cargas distribuidas
   ```

3. **Implementar cálculo de M(x) para barra**
   ```python
   def calcular_M_barra(barra, reacciones, cargas):
       # M(x) = Mi + Vi*x - ∫∫q(x)dx
       # Usar TERNA para signos correctos
   ```

**Tests:**
- `test_esfuerzos_viga_simple.py`: Viga simplemente apoyada con P central
  - Verificar V(0) = P/2, V(L) = -P/2
  - Verificar M(L/2) = P·L/4

#### Semana 2: Casos complejos
**Tareas:**
4. **Cargas distribuidas (uniformes, triangulares, trapezoidales)**
   ```python
   def calcular_M_con_carga_distribuida(q1, q2, x):
       # M por carga trapezoidal
   ```

5. **Múltiples cargas en una barra**
   - Dividir barra en tramos
   - Calcular esfuerzos por tramo
   - Unificar en funciones continuas

6. **Integración con motor principal**
   ```python
   # En motor_fuerzas.py:
   def calcular_esfuerzos_todas_subestructuras(self):
       for sub in [self.fundamental] + self.subestructuras_Xi:
           for barra in sub.barras:
               diagrama = calcular_esfuerzos_barra(barra, sub.reacciones)
               sub.diagramas[barra.id] = diagrama
   ```

**Tests:**
- `test_esfuerzos_viga_distribuida.py`: q uniforme
- `test_esfuerzos_multipunto.py`: Varias cargas puntuales

**Entregable:** Función `calcular_esfuerzos_viga_isostatica()` completamente funcional

---

### **FASE 2: TRABAJOS VIRTUALES (Semanas 3-4)**
**Objetivo:** Calcular coeficientes de flexibilidad fij y términos independientes e0i

#### Semana 3: Integración numérica
**Archivo:** `src/domain/analysis/trabajos_virtuales.py`

**Tareas:**
1. **Implementar integrador básico**
   ```python
   class CalculadorFlexibilidad:
       def calcular_fij(self, sub_i, sub_j, barra):
           # ∫ (Mi·Mj)/(E·Jz) dx + ∫ (Ni·Nj)/(E·A) dx
           integral_M = self._integrar_producto(
               sub_i.diagramas[barra.id].M,
               sub_j.diagramas[barra.id].M,
               barra.material.E * barra.seccion.Jz,
               barra.L
           )
           return integral_M  # + integral_N + integral_V
   ```

2. **Método de Simpson adaptativo**
   ```python
   def _integrar_producto(self, f1, f2, divisor, L):
       n = 21  # Puntos (impar para Simpson)
       x_vals = np.linspace(0, L, n)
       y_vals = [f1(x) * f2(x) / divisor for x in x_vals]
       return simpson(y_vals, x=x_vals)
   ```

3. **Cálculo de matriz [F] completa**
   ```python
   def ensamblar_matriz_F(self):
       n = len(self.subestructuras_Xi)
       F = np.zeros((n, n))
       for i in range(n):
           for j in range(n):
               F[i,j] = self.calcular_fij(
                   self.subestructuras_Xi[i],
                   self.subestructuras_Xi[j]
               )
       # Verificar simetría
       assert np.allclose(F, F.T, atol=1e-10)
       return F
   ```

#### Semana 4: Términos independientes
**Tareas:**
4. **Cálculo de e0i**
   ```python
   def calcular_e0i(self, sub_i):
       # e0i = ∫ (Mi·M0)/(E·Jz) dx
       e0 = 0.0
       for barra in self.modelo.barras:
           e0 += self._integrar_producto(
               sub_i.diagramas[barra.id].M,
               self.fundamental.diagramas[barra.id].M,
               barra.material.E * barra.seccion.Jz,
               barra.L
           )
       return e0
   ```

5. **Vector {e₀} completo**
   ```python
   def ensamblar_vector_e0(self):
       n = len(self.subestructuras_Xi)
       e0 = np.zeros(n)
       for i in range(n):
           e0[i] = self.calcular_e0i(self.subestructuras_Xi[i])
       return e0
   ```

**Tests:**
- `test_trabajos_virtuales_viga.py`: Viga biempotrada
  - Comparar fij con solución analítica

**Entregable:** Clase `CalculadorFlexibilidad` funcional

---

### **FASE 3: SOLVER SECE (Semana 5)**
**Objetivo:** Resolver [F]·{X} = -{e₀} y obtener redundantes

#### Semana 5: Resolución numérica
**Archivo:** `src/domain/analysis/sece_solver.py`

**Tareas:**
1. **Implementar solver principal**
   ```python
   class SolverSECE:
       def resolver(self, F, e0):
           # Verificar condicionamiento
           cond = np.linalg.cond(F)
           if cond > 1e12:
               raise ValueError(f"Matriz mal condicionada: {cond:.2e}")

           # Resolver sistema
           X = np.linalg.solve(F, -e0)

           # Validar solución
           residual = np.linalg.norm(F @ X + e0)
           if residual > 1e-8:
               warnings.warn(f"Residual alto: {residual:.2e}")

           return X
   ```

2. **Integración con motor**
   ```python
   # En motor_fuerzas.py:
   def resolver(self):
       # 1. Generar subestructuras
       self.generar_subestructuras()

       # 2. Calcular esfuerzos
       self.calcular_esfuerzos_todas_subestructuras()

       # 3. Trabajos virtuales
       calc_flex = CalculadorFlexibilidad(self)
       self.matriz_F = calc_flex.ensamblar_matriz_F()
       self.vector_e0 = calc_flex.ensamblar_vector_e0()

       # 4. Resolver SECE
       solver = SolverSECE()
       self.solucion_X = solver.resolver(self.matriz_F, self.vector_e0)

       # 5. Superposición
       self.calcular_resultados_finales()
   ```

**Tests:**
- `test_sece_viga_biempotrada.py`: GH=3
  - Verificar X contra solución manual

**Entregable:** Solver SECE funcionando

---

### **FASE 4: SUPERPOSICIÓN (Semana 6)**
**Objetivo:** Combinar resultados de todas las subestructuras

#### Semana 6: Resultados finales
**Archivo:** `src/domain/analysis/motor_fuerzas.py`

**Tareas:**
1. **Superposición de diagramas**
   ```python
   def calcular_resultados_finales(self):
       self.diagramas_finales = {}

       for barra in self.modelo.barras:
           # Diagrama fundamental
           M0 = self.fundamental.diagramas[barra.id].M
           V0 = self.fundamental.diagramas[barra.id].V
           N0 = self.fundamental.diagramas[barra.id].N

           # Superposición
           def M_final(x):
               suma = M0(x)
               for i, Xi in enumerate(self.solucion_X):
                   Mi = self.subestructuras_Xi[i].diagramas[barra.id].M
                   suma += Xi * Mi(x)
               return suma

           # Guardar
           self.diagramas_finales[barra.id] = DiagramaEsfuerzos(
               barra_id=barra.id,
               L=barra.L,
               _M_func=M_final,
               _V_func=V_final,
               _N_func=N_final
           )
   ```

2. **Superposición de reacciones**
   ```python
   def calcular_reacciones_finales(self):
       self.reacciones_finales = {}

       for nudo_id in self.fundamental.reacciones:
           R0 = self.fundamental.reacciones[nudo_id]
           Rx_final = R0[0]
           Ry_final = R0[1]
           Mz_final = R0[2]

           for i, Xi in enumerate(self.solucion_X):
               Ri = self.subestructuras_Xi[i].reacciones[nudo_id]
               Rx_final += Xi * Ri[0]
               Ry_final += Xi * Ri[1]
               Mz_final += Xi * Ri[2]

           self.reacciones_finales[nudo_id] = np.array([
               Rx_final, Ry_final, Mz_final
           ])
   ```

3. **Verificación de equilibrio**
   ```python
   def verificar_equilibrio(self):
       Fx_total = sum(r[0] for r in self.reacciones_finales.values())
       Fy_total = sum(r[1] for r in self.reacciones_finales.values())

       # Sumar cargas externas
       Fx_cargas = sum(c.Fx for c in self.modelo.cargas_puntuales_nudo)
       Fy_cargas = sum(c.Fy for c in self.modelo.cargas_puntuales_nudo)

       assert abs(Fx_total + Fx_cargas) < 1e-6, "Falla equilibrio en X"
       assert abs(Fy_total + Fy_cargas) < 1e-6, "Falla equilibrio en Y"
   ```

**Tests:**
- `test_superposicion_viga.py`: Verificar M_final contra teoría

**Entregable:** Método `resolver()` end-to-end funcionando

---

### **FASE 5: VISUALIZACIÓN (Semana 7)**
**Objetivo:** Dibujar diagramas N, V, M en el canvas

#### Semana 7: Diagramas gráficos
**Archivo:** `src/gui/canvas/structure_canvas.py`

**Tareas:**
1. **Dibujar diagrama de momentos**
   ```python
   def _draw_diagrama_momentos(self, painter, barra, diagrama):
       n_puntos = 21
       puntos_offset = []

       for i in range(n_puntos):
           x_local = i * barra.L / (n_puntos - 1)
           M = diagrama.M(x_local)

           # Posición en el mundo
           t = x_local / barra.L
           x_world = barra.nudo_i.x + t * (barra.nudo_j.x - barra.nudo_i.x)
           y_world = barra.nudo_i.y + t * (barra.nudo_j.y - barra.nudo_i.y)

           # Offset perpendicular
           ang_perp = barra.angulo + math.pi/2
           escala = 0.05  # m/kNm (ajustable)
           offset_x = M * escala * math.cos(ang_perp)
           offset_y = M * escala * math.sin(ang_perp)

           pos = self._world_to_scene(x_world + offset_x, y_world + offset_y)
           puntos_offset.append(pos)

       # Dibujar polilínea
       painter.setPen(QPen(QColor(200, 0, 0), 2))  # Rojo para M
       for i in range(len(puntos_offset) - 1):
           painter.drawLine(puntos_offset[i], puntos_offset[i+1])
   ```

2. **Toggle para mostrar N, V, M**
   - Botones en toolbar: "Mostrar N", "Mostrar V", "Mostrar M"
   - `self._show_N = True/False`

3. **Escala automática y manual**
   - Encontrar M_max, V_max, N_max en toda la estructura
   - Ajustar escala para que quepa en pantalla
   - Slider para ajuste manual

**Tests:**
- Visual: Crear viga simple, verificar que diagrama M tiene forma de triángulo

**Entregable:** Diagramas visuales funcionando

---

### **FASE 6: VALIDACIÓN (Semana 8)**
**Objetivo:** Validar todo el sistema con casos clásicos

#### Semana 8: Suite de tests
**Directorio:** `tests/integration/`

**Casos a implementar:**

**1. Viga biempotrada (GH=3)**
```python
def test_viga_biempotrada():
    # Geometría: L=6m
    # Carga: P=10kN en centro
    # Redundantes: Ma, Mb, Vb

    # Solución teórica:
    # Ma = -PL/8 = -7.5 kNm
    # Mb = PL/8 = 7.5 kNm
    # Va = Vb = P/2 = 5 kN

    modelo = crear_viga_biempotrada(L=6, P=10)
    motor = MotorMetodoFuerzas(modelo)
    resultado = motor.resolver()

    assert abs(resultado.reacciones_finales[1][2] + 7.5) < 0.01  # Ma
    assert abs(resultado.reacciones_finales[2][2] - 7.5) < 0.01  # Mb
```

**2. Viga continua 2 vanos (GH=1)**
```python
def test_viga_continua_2_vanos():
    # Redundante: Rc_y (reacción en apoyo central)
    # Verificar contra teoría de tres momentos
```

**3. Pórtico rectangular (GH=3)**
```python
def test_portico_rectangular():
    # 2 columnas empotradas + 1 viga
    # Carga horizontal en nudo superior
```

**4. Marco con carga distribuida**
```python
def test_marco_carga_distribuida():
    # Verificar integración de cargas distribuidas
```

**Tests esperados:**
- 10 casos clásicos validados
- Error < 1% respecto solución analítica
- Suite ejecutable con `pytest tests/integration/`

**Entregable:** Suite completa de validación ✓

---

## 📦 FUNCIONALIDADES OPCIONALES (POST-MVP)

### **FASE 7: DEFORMADAS (Opcional)**
**Semana 9:**
- Calcular desplazamientos en nudos
- Dibujar deformada exagerada
- Línea elástica de barras

### **FASE 8: EXPORTACIÓN (Opcional)**
**Semana 10:**
- Exportar PNG/PDF de diagramas (matplotlib)
- Exportar CSV de resultados
- Generar reporte técnico PDF (ReportLab)

### **FASE 9: CARGAS ESPECIALES (Opcional)**
**Semana 11:**
- Cargas térmicas (ΔT)
- Movimientos impuestos (hundimientos)
- Resortes elásticos (kx, ky, kθ)

### **FASE 10: GUARDADO/CARGA (Opcional)**
**Semana 12:**
- Serialización JSON del modelo completo
- Auto-guardado
- Historial (Undo/Redo)

---

## 🎯 HITOS CLAVE

| Hito | Fecha Estimada | Criterio de Éxito |
|------|----------------|-------------------|
| **M1:** Esfuerzos completos | Semana 2 | test_esfuerzos_*.py pasan ✓ |
| **M2:** Trabajos virtuales | Semana 4 | Matriz [F] simétrica calculada ✓ |
| **M3:** SECE resuelto | Semana 5 | Redundantes correctos en viga biempotrada ✓ |
| **M4:** Motor end-to-end | Semana 6 | Caso GH=3 completo sin errores ✓ |
| **M5:** Visualización | Semana 7 | Diagramas M visibles en GUI ✓ |
| **M6:** Validación completa | Semana 8 | 10 casos clásicos validados ✓ |

---

## 🚀 CÓMO CONTINUAR

### **Paso 1: Configurar entorno**
```bash
cd py-anes-mf
pip install -r requirements.txt
```

### **Paso 2: Ejecutar tests actuales**
```bash
pytest test_reacciones_simple.py -v
```
**Resultado esperado:** ✓ PASSED

### **Paso 3: Ejecutar aplicación**
```bash
python main.py
```
**Probar:**
1. Crear viga empotrada (0,0) a (6,0)
2. Empotramiento en (0,0)
3. Carga 10kN en x=3, ángulo +90°
4. Resolver → Ver reacciones verdes ✓

### **Paso 4: Comenzar Fase 1**
**Archivo a editar:** `src/domain/mechanics/esfuerzos.py`

**Función a completar:**
```python
def calcular_esfuerzos_viga_isostatica(
    barra: Barra,
    reacciones: Dict[int, np.ndarray],
    cargas: List[Carga]
) -> DiagramaEsfuerzos:
    """
    TODO: Implementar cálculo completo de N(x), V(x), M(x).

    PRÓXIMOS PASOS:
    1. Dividir barra en tramos (entre cargas puntuales)
    2. Para cada tramo, calcular N, V, M como funciones
    3. Verificar signos con TERNA
    4. Retornar DiagramaEsfuerzos completo
    """
    pass
```

**Test a crear:**
```bash
touch tests/integration/test_esfuerzos_viga_simple.py
```

---

## 📚 DOCUMENTACIÓN DE REFERENCIA

### **Archivos clave:**
- `claude.md`: Especificación completa del proyecto
- `ARQUITECTURA_PROYECTO.md`: Flujo de ejecución
- `SISTEMA_COORDENADAS_LOCALES.md`: Convenciones de signos
- `REFERENCIA_RAPIDA_ANGULOS.txt`: Ángulos y TERNA

### **Fórmulas importantes:**
```
TERNA:
  X+ derecha
  Y+ abajo
  Mz+ horario

Equilibrio:
  ΣFx = 0
  ΣFy = 0
  ΣMz = 0 (respecto a cualquier punto)

Momentos:
  M(punto) = -Fy × (x_punto - x_fuerza) + Fx × (y_punto - y_fuerza)

Trabajos virtuales:
  fij = ∫ (Mi·Mj)/(E·Jz) dx
  e0i = ∫ (Mi·M0)/(E·Jz) dx

SECE:
  [F]·{X} = -{e0}
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

Antes de marcar una fase como completa:

### Fase 1 - Esfuerzos:
- [ ] N(x) correcto para carga axial
- [ ] V(x) correcto para carga puntual
- [ ] V(x) correcto para carga distribuida
- [ ] M(x) correcto con TERNA
- [ ] Test viga simple pasa
- [ ] Test viga distribuida pasa

### Fase 2 - Trabajos Virtuales:
- [ ] Integración numérica implementada
- [ ] Matriz [F] es simétrica (|F - F.T| < 1e-10)
- [ ] Vector {e0} calculado
- [ ] Test comparación con fórmula analítica pasa

### Fase 3 - SECE:
- [ ] Solver resuelve sin errores
- [ ] Condicionamiento verificado
- [ ] Residual < 1e-8
- [ ] Test viga biempotrada da redundantes correctos

### Fase 4 - Superposición:
- [ ] Diagramas finales calculados
- [ ] Reacciones finales calculadas
- [ ] Equilibrio verificado (ΣF=0, ΣM=0)

### Fase 5 - Visualización:
- [ ] Diagrama M dibujado correctamente
- [ ] Diagrama V dibujado correctamente
- [ ] Diagrama N dibujado correctamente
- [ ] Escala ajustable funciona

### Fase 6 - Validación:
- [ ] 10 casos clásicos implementados
- [ ] Error < 1% en todos los casos
- [ ] Documentación de cada caso

---

## 🔧 HERRAMIENTAS Y COMANDOS ÚTILES

### **Ejecutar tests:**
```bash
pytest tests/ -v                    # Todos los tests
pytest tests/integration/ -v        # Solo integración
pytest -k "viga" -v                 # Tests que contengan "viga"
pytest --cov=src tests/             # Con cobertura
```

### **Linting:**
```bash
flake8 src/                         # Verificar PEP 8
black src/                          # Auto-formatear código
```

### **Debugging:**
```python
# En cualquier archivo:
import pdb; pdb.set_trace()         # Breakpoint
```

### **Visualizar matriz [F]:**
```python
import matplotlib.pyplot as plt
plt.imshow(F, cmap='viridis')
plt.colorbar()
plt.title("Matriz de Flexibilidad")
plt.show()
```

---

## 📞 CONTACTO Y SOPORTE

**En caso de dudas sobre:**
- **Teoría del Método de Fuerzas:** Revisar PDFs en `Informacion adicional/`
- **Convenciones de signos:** `SISTEMA_COORDENADAS_LOCALES.md`
- **Arquitectura del código:** `ARQUITECTURA_PROYECTO.md`
- **Fórmulas específicas:** `claude.md` sección 9.2

---

## 🎉 ÉXITO FINAL

El proyecto estará **100% funcional** cuando:

✅ Usuario puede crear estructura en GUI
✅ Usuario puede aplicar vínculos y cargas
✅ Sistema calcula GH automáticamente
✅ Sistema resuelve SECE sin errores
✅ Diagramas N, V, M se muestran correctamente
✅ Reacciones coinciden con teoría (error < 1%)
✅ Suite de 10 tests clásicos pasa

**ENTONCES:** Sistema listo para uso profesional y pedagógico! 🚀

---

**Última actualización:** 11/02/2025
**Versión:** 0.2.0-dev
**Estado:** Motor de reacciones ✓, Esfuerzos 40%, Trabajos virtuales 0%
