"""
Tests unitarios para ModeloEstructural.

Verifica:
- Creación y gestión del modelo
- Cálculo del grado de hiperestaticidad
- Validación de la estructura
"""

import pytest

from src.domain.entities.vinculo import Empotramiento, ApoyoFijo, Rodillo
from src.domain.entities.carga import CargaPuntualNudo, CargaDistribuida
from src.domain.model.modelo_estructural import ModeloEstructural


class TestModeloEstructural:
    """Tests para ModeloEstructural."""

    def test_crear_modelo_vacio(self, modelo_vacio):
        """Debe crear modelo sin elementos."""
        assert modelo_vacio.num_nudos == 0
        assert modelo_vacio.num_barras == 0
        assert modelo_vacio.num_cargas == 0

    def test_agregar_nudo(self, modelo_vacio):
        """Debe agregar nudo correctamente."""
        n = modelo_vacio.agregar_nudo(0, 0, "A")
        assert modelo_vacio.num_nudos == 1
        assert n.id == 1
        assert n.nombre == "A"

    def test_agregar_nudos_duplicados(self, modelo_vacio):
        """Debe rechazar nudos en la misma posición."""
        modelo_vacio.agregar_nudo(0, 0, "A")
        with pytest.raises(ValueError, match="Ya existe un nudo"):
            modelo_vacio.agregar_nudo(0, 0, "B")

    def test_agregar_barra(self, modelo_vacio, acero_a36, seccion_ipe220):
        """Debe agregar barra entre nudos existentes."""
        n1 = modelo_vacio.agregar_nudo(0, 0, "A")
        n2 = modelo_vacio.agregar_nudo(6, 0, "B")
        b = modelo_vacio.agregar_barra(n1, n2, acero_a36, seccion_ipe220, "Viga")

        assert modelo_vacio.num_barras == 1
        assert b.id == 1
        assert abs(b.L - 6.0) < 1e-10

    def test_asignar_vinculo(self, modelo_vacio):
        """Debe asignar vínculo a nudo."""
        n = modelo_vacio.agregar_nudo(0, 0, "A")
        modelo_vacio.asignar_vinculo(n.id, Empotramiento())

        assert n.tiene_vinculo
        assert modelo_vacio.num_vinculos == 1
        assert modelo_vacio.num_reacciones == 3  # Empotramiento = 3 GDL

    def test_agregar_carga(self, modelo_vacio):
        """Debe agregar cargas al modelo."""
        n = modelo_vacio.agregar_nudo(0, 0, "A")
        carga = CargaPuntualNudo(nudo=n, Fx=10, Fy=-20, Mz=0)
        modelo_vacio.agregar_carga(carga)

        assert modelo_vacio.num_cargas == 1
        assert len(modelo_vacio.cargas_nodales) == 1


class TestGradoHiperestaticidad:
    """Tests para el cálculo del grado de hiperestaticidad."""

    def test_viga_biempotrada_gh3(self, modelo_viga_biempotrada):
        """Viga biempotrada debe ser hiperestática de grado 3."""
        gh = modelo_viga_biempotrada.grado_hiperestaticidad

        # GH = r + 3c - 3n = 6 + 3(1) - 3(2) = 6 + 3 - 6 = 3
        assert gh == 3
        assert modelo_viga_biempotrada.es_hiperestatica
        assert "grado 3" in modelo_viga_biempotrada.clasificacion_estatica

    def test_viga_simplemente_apoyada_gh0(self, modelo_viga_simplemente_apoyada):
        """Viga simplemente apoyada debe ser isostática."""
        gh = modelo_viga_simplemente_apoyada.grado_hiperestaticidad

        # GH = r + 3c - 3n = 3 + 3(1) - 3(2) = 3 + 3 - 6 = 0
        assert gh == 0
        assert modelo_viga_simplemente_apoyada.es_isostatica

    def test_portico_simple_gh3(self, modelo_portico_simple):
        """Pórtico simple biempotrado debe ser hiperestático de grado 3."""
        gh = modelo_portico_simple.grado_hiperestaticidad

        # 4 nudos, 3 barras, 2 empotramientos (6 reacciones)
        # GH = r + 3c - 3n = 6 + 3(3) - 3(4) = 6 + 9 - 12 = 3
        assert gh == 3
        assert modelo_portico_simple.es_hiperestatica

    def test_estructura_hipostatica(self, modelo_vacio, acero_a36, seccion_ipe220):
        """Estructura sin vínculos suficientes debe ser hipostática."""
        n1 = modelo_vacio.agregar_nudo(0, 0, "A")
        n2 = modelo_vacio.agregar_nudo(6, 0, "B")
        modelo_vacio.agregar_barra(n1, n2, acero_a36, seccion_ipe220)

        # Sin vínculos: GH = 0 + 3(1) - 3(2) = 3 - 6 = -3
        modelo_vacio.asignar_vinculo(n1.id, Rodillo(direccion="Uy"))  # Solo 1 reacción

        gh = modelo_vacio.grado_hiperestaticidad
        assert gh < 0
        assert modelo_vacio.es_hipostatica


class TestValidacionModelo:
    """Tests para la validación del modelo."""

    def test_modelo_valido(self, modelo_viga_biempotrada):
        """Modelo bien construido debe ser válido."""
        errores = modelo_viga_biempotrada.validar()
        # Puede haber advertencias pero no errores críticos para esta estructura
        assert modelo_viga_biempotrada.es_valido or len(errores) == 0

    def test_modelo_sin_nudos(self, modelo_vacio):
        """Modelo sin nudos debe reportar error."""
        errores = modelo_vacio.validar()
        assert any("nudos" in e.lower() for e in errores)

    def test_modelo_sin_vinculos(self, modelo_vacio, acero_a36, seccion_ipe220):
        """Modelo sin vínculos debe reportar error."""
        n1 = modelo_vacio.agregar_nudo(0, 0)
        n2 = modelo_vacio.agregar_nudo(6, 0)
        modelo_vacio.agregar_barra(n1, n2, acero_a36, seccion_ipe220)

        errores = modelo_vacio.validar()
        assert any("vínculo" in e.lower() for e in errores)


class TestGeometriaModelo:
    """Tests para propiedades geométricas del modelo."""

    def test_bounding_box(self, modelo_portico_simple):
        """El bounding box debe calcularse correctamente."""
        bbox = modelo_portico_simple.bounding_box

        # Pórtico: x de 0 a 6, y de 0 a 3
        x_min, y_min, x_max, y_max = bbox
        assert abs(x_min - 0.0) < 1e-10
        assert abs(y_min - 0.0) < 1e-10
        assert abs(x_max - 6.0) < 1e-10
        assert abs(y_max - 3.0) < 1e-10

    def test_centro_geometrico(self, modelo_portico_simple):
        """El centro geométrico debe calcularse correctamente."""
        centro = modelo_portico_simple.centro_geometrico

        # 4 nudos: (0,0), (6,0), (0,3), (6,3) -> centro en (3, 1.5)
        assert abs(centro[0] - 3.0) < 1e-10
        assert abs(centro[1] - 1.5) < 1e-10


class TestArticulacionesInternas:
    """Tests para articulaciones internas (rótulas)."""

    def test_agregar_articulacion_extremo_i(self, modelo_viga_biempotrada):
        """Agregar articulación en extremo i."""
        barra = modelo_viga_biempotrada.barras[0]

        modelo_viga_biempotrada.agregar_articulacion(barra.id, "i")

        assert barra.articulacion_i is True
        assert barra.articulacion_j is False
        assert modelo_viga_biempotrada.num_articulaciones_internas == 1

    def test_agregar_articulacion_extremo_j(self, modelo_viga_biempotrada):
        """Agregar articulación en extremo j."""
        barra = modelo_viga_biempotrada.barras[0]

        modelo_viga_biempotrada.agregar_articulacion(barra.id, "j")

        assert barra.articulacion_i is False
        assert barra.articulacion_j is True

    def test_articulacion_reduce_gh(self, modelo_viga_biempotrada):
        """Una articulación interna debe reducir GH en 1."""
        gh_inicial = modelo_viga_biempotrada.grado_hiperestaticidad
        barra = modelo_viga_biempotrada.barras[0]

        modelo_viga_biempotrada.agregar_articulacion(barra.id, "i")

        gh_final = modelo_viga_biempotrada.grado_hiperestaticidad
        assert gh_final == gh_inicial - 1

    def test_dos_articulaciones_reducen_gh_en_2(self, modelo_vacio, acero_a36, seccion_ipe220):
        """Dos articulaciones deben reducir GH en 2."""
        # Crear modelo fresco para este test
        n1 = modelo_vacio.agregar_nudo(0, 0, "A")
        n2 = modelo_vacio.agregar_nudo(6, 0, "B")
        barra = modelo_vacio.agregar_barra(n1, n2, acero_a36, seccion_ipe220)
        modelo_vacio.asignar_vinculo(n1.id, Empotramiento())
        modelo_vacio.asignar_vinculo(n2.id, Empotramiento())

        gh_inicial = modelo_vacio.grado_hiperestaticidad  # Debe ser 3

        modelo_vacio.agregar_articulacion(barra.id, "i")
        modelo_vacio.agregar_articulacion(barra.id, "j")

        gh_final = modelo_vacio.grado_hiperestaticidad
        assert gh_inicial == 3, f"GH inicial esperado: 3, obtenido: {gh_inicial}"
        assert gh_final == 1, f"GH final esperado: 1, obtenido: {gh_final}"
        assert modelo_vacio.num_articulaciones_internas == 2

    def test_remover_articulacion(self, modelo_viga_biempotrada):
        """Remover articulación debe restaurar GH."""
        barra = modelo_viga_biempotrada.barras[0]
        gh_inicial = modelo_viga_biempotrada.grado_hiperestaticidad

        modelo_viga_biempotrada.agregar_articulacion(barra.id, "i")
        modelo_viga_biempotrada.remover_articulacion(barra.id, "i")

        assert modelo_viga_biempotrada.grado_hiperestaticidad == gh_inicial
        assert modelo_viga_biempotrada.num_articulaciones_internas == 0

    def test_barras_con_articulacion(self, modelo_portico_simple):
        """Debe listar correctamente las barras con articulaciones."""
        barras = modelo_portico_simple.barras

        modelo_portico_simple.agregar_articulacion(barras[0].id, "i")
        modelo_portico_simple.agregar_articulacion(barras[1].id, "j")

        barras_art = modelo_portico_simple.barras_con_articulacion
        assert len(barras_art) == 2


class TestEstadoModelo:
    """Tests para el estado del modelo."""

    def test_modelo_modificado(self, modelo_vacio):
        """Agregar elementos debe marcar el modelo como modificado."""
        assert not modelo_vacio.esta_modificado  # Modelo recién creado

        modelo_vacio.agregar_nudo(0, 0)
        assert modelo_vacio.esta_modificado

    def test_marcar_guardado(self, modelo_vacio):
        """Marcar como guardado debe limpiar el flag de modificación."""
        modelo_vacio.agregar_nudo(0, 0)
        assert modelo_vacio.esta_modificado

        modelo_vacio.marcar_guardado()
        assert not modelo_vacio.esta_modificado

    def test_modelo_no_resuelto(self, modelo_viga_biempotrada):
        """Un modelo nuevo no debe estar resuelto."""
        assert not modelo_viga_biempotrada.esta_resuelto
